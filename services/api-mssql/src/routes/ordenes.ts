import { OpenAPIHono } from '@hono/zod-openapi';
import { prisma } from '../lib/prisma';
import { ordenQuerySchema } from '../validators/query-schemas';
import { listOrdenesRoute, getOrdenRoute } from './ordenes.openapi';

const ordenes = new OpenAPIHono();

// GET /ordenes - List all ordenes with pagination and filters
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
ordenes.openapi(listOrdenesRoute, async (c) => {
  try {
    const query = c.req.query();
    const validated = ordenQuerySchema.parse(query);

    // Build where clause for filters
    const where: any = {};
    
    if (validated.clienteId) {
      where.ClienteId = validated.clienteId;
    }
    if (validated.canal) {
      where.Canal = validated.canalExact === 'true'
        ? { equals: validated.canal }
        : { contains: validated.canal };
    }
    if (validated.moneda) {
      where.Moneda = { contains: validated.moneda };
    }
    if (validated.fechaDesde || validated.fechaHasta) {
      where.Fecha = {};
      if (validated.fechaDesde) {
        where.Fecha.gte = new Date(validated.fechaDesde);
      }
      if (validated.fechaHasta) {
        where.Fecha.lte = new Date(validated.fechaHasta);
      }
    }
    
    // Total field numeric filters
    if (validated.totalMin || validated.totalMax || validated.totalGt || validated.totalLt || validated.totalEq) {
      where.Total = {};
      if (validated.totalMin) {
        where.Total.gte = validated.totalMin;
      }
      if (validated.totalMax) {
        where.Total.lte = validated.totalMax;
      }
      if (validated.totalGt) {
        where.Total.gt = validated.totalGt;
      }
      if (validated.totalLt) {
        where.Total.lt = validated.totalLt;
      }
      if (validated.totalEq) {
        where.Total.equals = validated.totalEq;
      }
    }

    // Build order by
    const orderBy: any = {};
    if (validated.sortBy) {
      if (['Fecha', 'Canal', 'Moneda', 'Total'].includes(validated.sortBy)) {
        orderBy[validated.sortBy] = validated.sortOrder || 'asc';
      }
    } else {
      orderBy.OrdenId = 'asc';
    }

    // Calculate pagination
    const skip = (validated.page - 1) * validated.limit;

    // Get total count
    const total = await prisma.orden.count({ where });
    const totalPages = Math.ceil(total / validated.limit);

    // Get paginated data
    const data = await prisma.orden.findMany({
      where,
      orderBy,
      skip,
      take: validated.limit,
    });

    return c.json({
      success: true,
      data,
      pagination: {
        page: validated.page,
        limit: validated.limit,
        total,
        totalPages,
      },
    });
  } catch (error) {
    console.error('Error listing ordenes:', error);
    
    if (error instanceof Error && error.message.includes('validation')) {
      return c.json(
        {
          success: false,
          message: 'Invalid query parameters',
          error: error.message,
        },
        400
      );
    }

    return c.json(
      {
        success: false,
        message: 'Internal server error',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500
    );
  }
});

// GET /ordenes/:id - Get single orden by ID with optional relations
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
ordenes.openapi(getOrdenRoute, async (c) => {
  try {
    const id = parseInt(c.req.param('id'), 10);
    const include = c.req.query('include');

    if (isNaN(id)) {
      return c.json(
        {
          success: false,
          message: 'Invalid orden ID',
        },
        400
      );
    }

    // Parse includes
    const includes = include
      ? include.split(',').map((s) => s.trim().toLowerCase())
      : [];

    // Build include object for Prisma
    const includeObj: any = {};
    if (includes.includes('cliente')) {
      includeObj.cliente = true;
    }
    if (includes.includes('detalles')) {
      includeObj.detalles = {
        include: {
          producto: true,
        },
      };
    }

    const orden = await prisma.orden.findUnique({
      where: { OrdenId: id },
      include: includeObj,
    });

    if (!orden) {
      return c.json(
        {
          success: false,
          message: 'Orden not found',
        },
        404
      );
    }

    return c.json({
      success: true,
      data: orden,
    });
  } catch (error) {
    console.error('Error getting orden:', error);
    
    return c.json(
      {
        success: false,
        message: 'Internal server error',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      500
    );
  }
});

export default ordenes;
