/* =======================================================================
   BCCR Exchange Rate Jobs - SQL Server 2022 Developer Edition
   
   Este script implementa:
   1. Configuración de xp_cmdshell para llamadas HTTP con curl
   2. Stored Procedures para consultar el WebService del BCCR
   3. Carga inicial de tipos de cambio (últimos 3 años)
   4. Job de SQL Server Agent para actualización diaria a las 5:00 AM
   
   Requisitos:
   - SQL Server 2022 Developer Edition
   - SQL Server Agent habilitado (MSSQL_AGENT_ENABLED=true)
   - curl disponible en el contenedor (incluido en la imagen oficial)
   ======================================================================= */

USE DW_SALES;
GO

-- =========================================================================
-- 1) Habilitar xp_cmdshell (necesario para ejecutar curl)
-- =========================================================================
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;
GO

-- =========================================================================
-- 2) Crear esquema para jobs si no existe
-- =========================================================================
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'jobs')
    EXEC('CREATE SCHEMA jobs');
GO

-- =========================================================================
-- 3) Tabla de configuración del BCCR
-- =========================================================================
IF OBJECT_ID('jobs.BCCR_Config', 'U') IS NOT NULL
    DROP TABLE jobs.BCCR_Config;
GO

CREATE TABLE jobs.BCCR_Config (
    ConfigID INT IDENTITY(1,1) PRIMARY KEY,
    ParamName NVARCHAR(50) NOT NULL UNIQUE,
    ParamValue NVARCHAR(500) NOT NULL,
    Description NVARCHAR(200) NULL,
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

INSERT INTO jobs.BCCR_Config (ParamName, ParamValue, Description) VALUES
('BCCR_ENDPOINT', 'https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos', 'URL del WebService del BCCR'),
('BCCR_TOKEN', '<REMOVED_BCCR_TOKEN>', 'Token de autenticación del BCCR'),
('BCCR_EMAIL', '<REMOVED_BCCR_EMAIL>', 'Email registrado en BCCR'),
('BCCR_NOMBRE', '<REMOVED_BCCR_NAME>', 'Nombre registrado en BCCR'),
('INDICADOR_COMPRA', '317', 'Código del indicador de compra USD/CRC'),
('INDICADOR_VENTA', '318', 'Código del indicador de venta USD/CRC'),
('YEARS_HISTORICO', '3', 'Años de histórico a cargar en el init'),
('LAST_SUCCESSFUL_LOAD', '1900-01-01', 'Última fecha cargada exitosamente');
GO

-- =========================================================================
-- 4) Tabla de log para el job
-- =========================================================================
IF OBJECT_ID('jobs.BCCR_Log', 'U') IS NOT NULL
    DROP TABLE jobs.BCCR_Log;
GO

CREATE TABLE jobs.BCCR_Log (
    LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ExecutionDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    JobType NVARCHAR(20) NOT NULL,
    FechaConsulta DATE NULL,
    Status NVARCHAR(20) NOT NULL,
    Message NVARCHAR(MAX) NULL,
    TasaCompra DECIMAL(18,6) NULL,
    TasaVenta DECIMAL(18,6) NULL,
    DurationMs INT NULL
);

CREATE INDEX IX_BCCR_Log_Date ON jobs.BCCR_Log(ExecutionDate DESC);
GO

-- =========================================================================
-- 5) Tabla temporal para respuestas de curl
-- =========================================================================
IF OBJECT_ID('jobs.BCCR_CurlOutput', 'U') IS NOT NULL
    DROP TABLE jobs.BCCR_CurlOutput;
GO

CREATE TABLE jobs.BCCR_CurlOutput (
    LineID INT IDENTITY(1,1) PRIMARY KEY,
    OutputLine NVARCHAR(MAX) NULL
);
GO

-- =========================================================================
-- 6) Función para obtener valor de configuración
-- =========================================================================
IF OBJECT_ID('jobs.fn_GetBCCRConfig', 'FN') IS NOT NULL
    DROP FUNCTION jobs.fn_GetBCCRConfig;
GO

CREATE FUNCTION jobs.fn_GetBCCRConfig(@ParamName NVARCHAR(50))
RETURNS NVARCHAR(500)
AS
BEGIN
    DECLARE @Value NVARCHAR(500);
    SELECT @Value = ParamValue FROM jobs.BCCR_Config WHERE ParamName = @ParamName;
    RETURN @Value;
END;
GO

-- =========================================================================
-- 7) Stored Procedure: Consultar BCCR con curl
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_ConsultarIndicador', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_ConsultarIndicador;
GO

CREATE PROCEDURE jobs.sp_BCCR_ConsultarIndicador
    @Indicador NVARCHAR(10),
    @FechaInicio NVARCHAR(10),  -- Formato dd/mm/yyyy
    @FechaFinal NVARCHAR(10),   -- Formato dd/mm/yyyy
    @XMLResponse NVARCHAR(MAX) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Endpoint NVARCHAR(500) = jobs.fn_GetBCCRConfig('BCCR_ENDPOINT');
    DECLARE @Token NVARCHAR(100) = jobs.fn_GetBCCRConfig('BCCR_TOKEN');
    DECLARE @Email NVARCHAR(100) = jobs.fn_GetBCCRConfig('BCCR_EMAIL');
    DECLARE @Nombre NVARCHAR(100) = jobs.fn_GetBCCRConfig('BCCR_NOMBRE');
    
    -- Construir el comando curl
    DECLARE @CurlCmd NVARCHAR(4000);
    SET @CurlCmd = 'curl -s -X POST "' + @Endpoint + '" ' +
        '-H "Content-Type: application/x-www-form-urlencoded" ' +
        '-d "Indicador=' + @Indicador + 
        '&FechaInicio=' + @FechaInicio + 
        '&FechaFinal=' + @FechaFinal + 
        '&Nombre=' + REPLACE(@Nombre, ' ', '%20') + 
        '&SubNiveles=N' +
        '&CorreoElectronico=' + @Email + 
        '&Token=' + @Token + '"';
    
    -- Limpiar tabla temporal
    TRUNCATE TABLE jobs.BCCR_CurlOutput;
    
    -- Ejecutar curl
    INSERT INTO jobs.BCCR_CurlOutput (OutputLine)
    EXEC xp_cmdshell @CurlCmd;
    
    -- Concatenar todas las líneas de respuesta
    SELECT @XMLResponse = STRING_AGG(ISNULL(OutputLine, ''), '')
    FROM jobs.BCCR_CurlOutput
    WHERE OutputLine IS NOT NULL;
END;
GO

-- =========================================================================
-- 8) Stored Procedure: Guardar tipo de cambio individual
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_SaveExchangeRate', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_SaveExchangeRate;
GO

CREATE PROCEDURE jobs.sp_BCCR_SaveExchangeRate
    @Fecha DATE,
    @TasaCompra DECIMAL(18,6),
    @TasaVenta DECIMAL(18,6),
    @Fuente NVARCHAR(64) = 'BCCR WS'
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- CRC -> USD (se almacena la tasa reportada por el BCCR para compra)
        MERGE INTO stg.tipo_cambio AS target
        USING (SELECT @Fecha AS fecha, 'CRC' AS de, 'USD' AS a, @TasaCompra AS tasa) AS source
        ON target.fecha = source.fecha AND target.de = source.de AND target.a = source.a
        WHEN MATCHED THEN
            UPDATE SET tasa = source.tasa, fuente = @Fuente, LoadTS = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (fecha, de, a, tasa, fuente, LoadTS)
            VALUES (source.fecha, source.de, source.a, source.tasa, @Fuente, SYSDATETIME());
        
        -- USD -> CRC (tasa de venta reportada por el BCCR)
        MERGE INTO stg.tipo_cambio AS target
        USING (SELECT @Fecha AS fecha, 'USD' AS de, 'CRC' AS a, @TasaVenta AS tasa) AS source
        ON target.fecha = source.fecha AND target.de = source.de AND target.a = source.a
        WHEN MATCHED THEN
            UPDATE SET tasa = source.tasa, fuente = @Fuente, LoadTS = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (fecha, de, a, tasa, fuente, LoadTS)
            VALUES (source.fecha, source.de, source.a, source.tasa, @Fuente, SYSDATETIME());
        
        -- Actualizar DimTiempo con ambas referencias
        UPDATE dw.DimTiempo
        SET TC_CRC_USD = @TasaCompra,
            TC_USD_CRC = @TasaVenta
        WHERE Fecha = @Fecha;
        
        -- Actualizar última fecha cargada
        UPDATE jobs.BCCR_Config 
        SET ParamValue = CAST(@Fecha AS NVARCHAR(10)), UpdatedAt = SYSDATETIME()
        WHERE ParamName = 'LAST_SUCCESSFUL_LOAD' AND @Fecha > TRY_CAST(ParamValue AS DATE);
        
        COMMIT TRANSACTION;
        RETURN 0;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        RETURN -1;
    END CATCH
END;
GO

-- =========================================================================
-- 9) Stored Procedure: Cargar tipos de cambio del BCCR (rango de fechas)
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_CargarTiposCambio', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_CargarTiposCambio;
GO

CREATE PROCEDURE jobs.sp_BCCR_CargarTiposCambio
    @FechaInicio DATE,
    @FechaFinal DATE
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartTime DATETIME2 = SYSDATETIME();
    DECLARE @FechaInicioStr NVARCHAR(10) = FORMAT(@FechaInicio, 'dd/MM/yyyy');
    DECLARE @FechaFinalStr NVARCHAR(10) = FORMAT(@FechaFinal, 'dd/MM/yyyy');
    DECLARE @XMLCompra NVARCHAR(MAX);
    DECLARE @XMLVenta NVARCHAR(MAX);
    DECLARE @IndicadorCompra NVARCHAR(10) = jobs.fn_GetBCCRConfig('INDICADOR_COMPRA');
    DECLARE @IndicadorVenta NVARCHAR(10) = jobs.fn_GetBCCRConfig('INDICADOR_VENTA');
    
    -- Log inicio
    INSERT INTO jobs.BCCR_Log (JobType, Status, Message)
    VALUES ('CARGA', 'RUNNING', 'Iniciando carga desde ' + @FechaInicioStr + ' hasta ' + @FechaFinalStr);
    
    BEGIN TRY
        -- Consultar indicador de compra
        EXEC jobs.sp_BCCR_ConsultarIndicador @IndicadorCompra, @FechaInicioStr, @FechaFinalStr, @XMLCompra OUTPUT;
        
        -- Consultar indicador de venta
        EXEC jobs.sp_BCCR_ConsultarIndicador @IndicadorVenta, @FechaInicioStr, @FechaFinalStr, @XMLVenta OUTPUT;
        
        -- Parsear y almacenar datos
        DECLARE @DatosCompra TABLE (Fecha DATE, Valor DECIMAL(18,6));
        DECLARE @DatosVenta TABLE (Fecha DATE, Valor DECIMAL(18,6));
        
        -- Variables para parseo
        DECLARE @Pos INT = 1;
        DECLARE @FechaStart INT, @FechaEnd INT;
        DECLARE @ValorStart INT, @ValorEnd INT;
        DECLARE @FechaStr NVARCHAR(30);
        DECLARE @ValorStr NVARCHAR(30);
        
        -- Parsear compra
        SET @Pos = 1;
        WHILE @Pos < LEN(ISNULL(@XMLCompra, ''))
        BEGIN
            SET @FechaStart = CHARINDEX('<DES_FECHA>', @XMLCompra, @Pos);
            IF @FechaStart = 0 BREAK;
            SET @FechaStart = @FechaStart + 11;
            SET @FechaEnd = CHARINDEX('</DES_FECHA>', @XMLCompra, @FechaStart);
            IF @FechaEnd = 0 BREAK;
            SET @FechaStr = LEFT(SUBSTRING(@XMLCompra, @FechaStart, @FechaEnd - @FechaStart), 10);
            
            SET @ValorStart = CHARINDEX('<NUM_VALOR>', @XMLCompra, @FechaEnd);
            IF @ValorStart = 0 BREAK;
            SET @ValorStart = @ValorStart + 11;
            SET @ValorEnd = CHARINDEX('</NUM_VALOR>', @XMLCompra, @ValorStart);
            IF @ValorEnd = 0 BREAK;
            SET @ValorStr = SUBSTRING(@XMLCompra, @ValorStart, @ValorEnd - @ValorStart);
            
            INSERT INTO @DatosCompra (Fecha, Valor)
            SELECT TRY_CAST(@FechaStr AS DATE), TRY_CAST(@ValorStr AS DECIMAL(18,6))
            WHERE TRY_CAST(@FechaStr AS DATE) IS NOT NULL;
            
            SET @Pos = @ValorEnd;
        END
        
        -- Parsear venta
        SET @Pos = 1;
        WHILE @Pos < LEN(ISNULL(@XMLVenta, ''))
        BEGIN
            SET @FechaStart = CHARINDEX('<DES_FECHA>', @XMLVenta, @Pos);
            IF @FechaStart = 0 BREAK;
            SET @FechaStart = @FechaStart + 11;
            SET @FechaEnd = CHARINDEX('</DES_FECHA>', @XMLVenta, @FechaStart);
            IF @FechaEnd = 0 BREAK;
            SET @FechaStr = LEFT(SUBSTRING(@XMLVenta, @FechaStart, @FechaEnd - @FechaStart), 10);
            
            SET @ValorStart = CHARINDEX('<NUM_VALOR>', @XMLVenta, @FechaEnd);
            IF @ValorStart = 0 BREAK;
            SET @ValorStart = @ValorStart + 11;
            SET @ValorEnd = CHARINDEX('</NUM_VALOR>', @XMLVenta, @ValorStart);
            IF @ValorEnd = 0 BREAK;
            SET @ValorStr = SUBSTRING(@XMLVenta, @ValorStart, @ValorEnd - @ValorStart);
            
            INSERT INTO @DatosVenta (Fecha, Valor)
            SELECT TRY_CAST(@FechaStr AS DATE), TRY_CAST(@ValorStr AS DECIMAL(18,6))
            WHERE TRY_CAST(@FechaStr AS DATE) IS NOT NULL;
            
            SET @Pos = @ValorEnd;
        END
        
        -- Insertar datos combinados
        DECLARE @Insertados INT = 0;
        DECLARE @CurFecha DATE, @CurCompra DECIMAL(18,6), @CurVenta DECIMAL(18,6);
        
        DECLARE cur CURSOR FOR
            SELECT c.Fecha, c.Valor AS Compra, v.Valor AS Venta
            FROM @DatosCompra c
            INNER JOIN @DatosVenta v ON c.Fecha = v.Fecha
            ORDER BY c.Fecha;
        
        OPEN cur;
        FETCH NEXT FROM cur INTO @CurFecha, @CurCompra, @CurVenta;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC jobs.sp_BCCR_SaveExchangeRate @CurFecha, @CurCompra, @CurVenta, 'BCCR SQL Job';
            SET @Insertados = @Insertados + 1;
            FETCH NEXT FROM cur INTO @CurFecha, @CurCompra, @CurVenta;
        END
        
        CLOSE cur;
        DEALLOCATE cur;
        
        -- Log éxito
        INSERT INTO jobs.BCCR_Log (JobType, Status, Message, DurationMs)
        VALUES ('CARGA', 'SUCCESS', 
                'Cargados ' + CAST(@Insertados AS NVARCHAR(10)) + ' registros',
                DATEDIFF(MILLISECOND, @StartTime, SYSDATETIME()));
        
        PRINT 'Carga completada: ' + CAST(@Insertados AS NVARCHAR(10)) + ' registros';
        
    END TRY
    BEGIN CATCH
        INSERT INTO jobs.BCCR_Log (JobType, Status, Message, DurationMs)
        VALUES ('CARGA', 'ERROR', ERROR_MESSAGE(), DATEDIFF(MILLISECOND, @StartTime, SYSDATETIME()));
        
        PRINT 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;
GO

-- =========================================================================
-- 10) Stored Procedure: Cargar histórico (últimos N años)
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_CargarHistorico', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_CargarHistorico;
GO

CREATE PROCEDURE jobs.sp_BCCR_CargarHistorico
    @AñosAtras INT = 3
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @FechaInicio DATE = DATEADD(YEAR, -@AñosAtras, GETDATE());
    DECLARE @FechaFinal DATE = CAST(GETDATE() AS DATE);
    
    PRINT 'Cargando histórico de tipos de cambio...';
    PRINT 'Desde: ' + CAST(@FechaInicio AS NVARCHAR(10));
    PRINT 'Hasta: ' + CAST(@FechaFinal AS NVARCHAR(10));
    
    EXEC jobs.sp_BCCR_CargarTiposCambio @FechaInicio, @FechaFinal;
END;
GO

-- =========================================================================
-- 11) Stored Procedure: Cargar tipo de cambio de hoy
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_CargarHoy', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_CargarHoy;
GO

CREATE PROCEDURE jobs.sp_BCCR_CargarHoy
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Hoy DATE = CAST(GETDATE() AS DATE);
    
    -- Verificar si ya se cargó hoy
    IF EXISTS (SELECT 1 FROM stg.tipo_cambio WHERE fecha = @Hoy AND de = 'USD' AND a = 'CRC')
    BEGIN
        INSERT INTO jobs.BCCR_Log (JobType, Status, Message)
        VALUES ('DIARIO', 'SKIPPED', 'Ya existe tipo de cambio para hoy');
        RETURN;
    END
    
    -- NOTE: El BCCR publica tipos de cambio todos los días, incluyendo fines de semana
    -- (usa el valor del último día hábil)
    
    -- Cargar tipo de cambio de hoy
    EXEC jobs.sp_BCCR_CargarTiposCambio @Hoy, @Hoy;
END;
GO

-- =========================================================================
-- 12) Stored Procedure: Verificar estado
-- =========================================================================
IF OBJECT_ID('jobs.sp_BCCR_CheckStatus', 'P') IS NOT NULL
    DROP PROCEDURE jobs.sp_BCCR_CheckStatus;
GO

CREATE PROCEDURE jobs.sp_BCCR_CheckStatus
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @LastLoad DATE;
    DECLARE @TotalRecords INT;
    DECLARE @TodayRateUSDCRC DECIMAL(18,6);
    DECLARE @TodayRateCRCUSD DECIMAL(18,6);
    
    SELECT @LastLoad = TRY_CAST(ParamValue AS DATE)
    FROM jobs.BCCR_Config WHERE ParamName = 'LAST_SUCCESSFUL_LOAD';
    
    SELECT @TotalRecords = COUNT(DISTINCT fecha) FROM stg.tipo_cambio;
    
    SELECT @TodayRateUSDCRC = tasa FROM stg.tipo_cambio 
    WHERE fecha = CAST(GETDATE() AS DATE) AND de = 'USD' AND a = 'CRC';

    SELECT @TodayRateCRCUSD = tasa FROM stg.tipo_cambio 
    WHERE fecha = CAST(GETDATE() AS DATE) AND de = 'CRC' AND a = 'USD';
    
    SELECT 
        @LastLoad AS UltimaCarga,
        @TotalRecords AS TotalDiasRegistrados,
        @TodayRateUSDCRC AS TasaHoy_USD_CRC,
        @TodayRateCRCUSD AS TasaHoy_CRC_USD,
        CASE 
            WHEN @TodayRateUSDCRC IS NOT NULL AND @TodayRateCRCUSD IS NOT NULL THEN 'OK'
            WHEN @LastLoad >= DATEADD(DAY, -1, CAST(GETDATE() AS DATE)) THEN 'WARNING - Pendiente hoy'
            ELSE 'ERROR - Atrasado'
        END AS Estado;
    
    SELECT TOP 10 * FROM jobs.BCCR_Log ORDER BY ExecutionDate DESC;
END;
GO

-- =========================================================================
-- 13) Vista para tipos de cambio
-- =========================================================================
IF OBJECT_ID('jobs.vw_TiposCambio', 'V') IS NOT NULL
    DROP VIEW jobs.vw_TiposCambio;
GO

CREATE VIEW jobs.vw_TiposCambio AS
SELECT 
    tc_usd.fecha AS Fecha,
    tc_usd.tasa AS USD_a_CRC,
    tc_crc.tasa AS CRC_a_USD,
    tc_usd.fuente AS Fuente,
    tc_usd.LoadTS AS UltimaActualizacion
FROM stg.tipo_cambio tc_usd
INNER JOIN stg.tipo_cambio tc_crc 
    ON tc_usd.fecha = tc_crc.fecha
WHERE tc_usd.de = 'USD' AND tc_usd.a = 'CRC'
  AND tc_crc.de = 'CRC' AND tc_crc.a = 'USD';
GO

-- =========================================================================
-- 14) Crear Job de SQL Server Agent
-- =========================================================================
USE msdb;
GO

-- Eliminar job si existe
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = N'BCCR_TipoCambio_Diario')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = N'BCCR_TipoCambio_Diario', @delete_unused_schedule = 1;
END
GO

-- Crear el job
EXEC msdb.dbo.sp_add_job
    @job_name = N'BCCR_TipoCambio_Diario',
    @enabled = 1,
    @description = N'Carga diaria de tipos de cambio del BCCR a las 5:00 AM',
    @category_name = N'Data Collector',
    @owner_login_name = N'sa';
GO

-- Agregar paso del job
EXEC msdb.dbo.sp_add_jobstep
    @job_name = N'BCCR_TipoCambio_Diario',
    @step_name = N'Cargar Tipo de Cambio',
    @step_id = 1,
    @subsystem = N'TSQL',
    @command = N'EXEC DW_SALES.jobs.sp_BCCR_CargarHoy;',
    @database_name = N'DW_SALES',
    @on_success_action = 1,  -- Quit with success
    @on_fail_action = 2;     -- Quit with failure
GO

-- Crear schedule para las 5:00 AM todos los días
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = N'BCCR_Schedule_5AM',
    @enabled = 1,
    @freq_type = 4,          -- Daily
    @freq_interval = 1,      -- Every 1 day
    @active_start_time = 50000;  -- 5:00:00 AM (formato HHMMSS)
GO

-- Asociar schedule al job
EXEC msdb.dbo.sp_attach_schedule
    @job_name = N'BCCR_TipoCambio_Diario',
    @schedule_name = N'BCCR_Schedule_5AM';
GO

-- Agregar job al servidor local
EXEC msdb.dbo.sp_add_jobserver
    @job_name = N'BCCR_TipoCambio_Diario',
    @server_name = N'(LOCAL)';
GO

USE DW_SALES;
GO

-- =========================================================================
-- 15) CARGAR DATOS HISTÓRICOS (3 años) - SOLO EN INIT
-- =========================================================================
PRINT '';
PRINT '============================================';
PRINT 'Iniciando carga de datos históricos del BCCR';
PRINT 'Esto puede tomar varios minutos...';
PRINT '============================================';
PRINT '';

-- Verificar si ya hay datos cargados
DECLARE @ExistingCount INT;
SELECT @ExistingCount = COUNT(*) FROM stg.tipo_cambio WHERE de = 'USD' AND a = 'CRC';

IF @ExistingCount < 100  -- Si hay menos de 100 registros, cargar histórico
BEGIN
    EXEC jobs.sp_BCCR_CargarHistorico @AñosAtras = 3;
END
ELSE
BEGIN
    PRINT 'Ya existen ' + CAST(@ExistingCount AS NVARCHAR(10)) + ' registros de tipos de cambio.';
    PRINT 'Se omite la carga histórica.';
END

-- =========================================================================
-- 16) Información final
-- =========================================================================
PRINT '';
PRINT '============================================';
PRINT 'Configuración de BCCR Jobs completada';
PRINT '';
PRINT 'STORED PROCEDURES DISPONIBLES:';
PRINT '  - jobs.sp_BCCR_CargarHistorico @AñosAtras=3';
PRINT '  - jobs.sp_BCCR_CargarHoy';
PRINT '  - jobs.sp_BCCR_CargarTiposCambio @FechaInicio, @FechaFinal';
PRINT '  - jobs.sp_BCCR_SaveExchangeRate @Fecha, @Compra, @Venta';
PRINT '  - jobs.sp_BCCR_CheckStatus';
PRINT '';
PRINT 'JOB DE SQL SERVER AGENT:';
PRINT '  - BCCR_TipoCambio_Diario (5:00 AM cada día)';
PRINT '';
PRINT 'Para verificar estado: EXEC jobs.sp_BCCR_CheckStatus';
PRINT '============================================';
GO
