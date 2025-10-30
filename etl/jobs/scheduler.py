"""
scheduler.py
Orquestador de jobs para actualizar tipos de cambio y otros procesos ETL.
Utiliza APScheduler para ejecutar tareas programadas.
"""

import sys
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Importar los jobs
from .bccr_tc_diario import actualizar_tipo_cambio_diario

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ETLScheduler:
    """Orquestador de jobs ETL usando APScheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def iniciar(self):
        """Inicia el scheduler y todos los jobs programados."""
        # Job diario: actualizar tipos de cambio a las 5:00 a.m.
        self.scheduler.add_job(
            actualizar_tipo_cambio_diario,
            CronTrigger(hour=5, minute=0),
            id="bccr_tc_diario",
            name="Actualizar tipos de cambio BCCR (diario a las 5:00 a.m.)",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler ETL iniciado. Jobs programados:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")

    def detener(self):
        """Detiene el scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler ETL detenido.")

    def listar_jobs(self):
        """Lista todos los jobs programados."""
        print("\nJobs programados:")
        if not self.scheduler.get_jobs():
            print("  No hay jobs programados.")
        else:
            for job in self.scheduler.get_jobs():
                print(f"  - {job.name}")
                print(f"    ID: {job.id}")
                print(f"    Trigger: {job.trigger}")

    def ejecutar_job_manualmente(self, job_id: str):
        """Ejecuta un job manualmente."""
        if job_id == "bccr_tc_diario":
            logger.info(f"Ejecutando job {job_id} manualmente...")
            actualizar_tipo_cambio_diario()
        else:
            logger.error(f"Job {job_id} no encontrado.")


if __name__ == "__main__":
    scheduler = ETLScheduler()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "start":
            logger.info("Iniciando scheduler ETL...")
            scheduler.iniciar()
            logger.info("El scheduler está corriendo. Presiona Ctrl+C para detener.")
            try:
                import time

                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Interrupción detectada. Deteniendo scheduler...")
                scheduler.detener()
        elif command == "list":
            scheduler.listar_jobs()
        elif command == "run" and len(sys.argv) > 2:
            job_id = sys.argv[2]
            scheduler.ejecutar_job_manualmente(job_id)
        else:
            print("Uso: python scheduler.py [start|list|run <job_id>]")
    else:
        print("Uso: python scheduler.py [start|list|run <job_id>]")
        print("  start     - Inicia el scheduler con todos los jobs")
        print("  list      - Lista los jobs programados")
        print(
            "  run       - Ejecuta un job manualmente (ej: python scheduler.py run bccr_tc_diario)"
        )
