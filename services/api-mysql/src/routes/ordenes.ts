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
      where.cliente_id = validated.clienteId;
    }
    if (validated.canal) {
      where.canal = validated.canalExact === 'true'
        ? { equals: validated.canal }
        : { contains: validated.canal, mode: 'insensitive' };
    }
    if (validated.moneda) {
      where.moneda = { contains: validated.moneda, mode: 'insensitive' };
    }
    if (validated.fechaDesde || validated.fechaHasta) {
      where.fecha = {};
      if (validated.fechaDesde) {
        where.fecha.gte = validated.fechaDesde;
      }
      if (validated.fechaHasta) {
        where.fecha.lte = validated.fechaHasta;
      }
    }
    
    // Total field numeric filters - Need to convert string to number
    if (validated.totalMin || validated.totalMax || validated.totalGt || validated.totalLt || validated.totalEq) {
      where.total = {};
      if (validated.totalMin) {
        where.total.gte = validated.totalMin.toString();
      }
      if (validated.totalMax) {
        where.total.lte = validated.totalMax.toString();
      }
      if (validated.totalGt) {
        where.total.gt = validated.totalGt.toString();
      }
      if (validated.totalLt) {
        where.total.lt = validated.totalLt.toString();
      }
      if (validated.totalEq) {
        where.total.equals = validated.totalEq.toString();
      }
    }

    // Build order by
    const orderBy: any = {};
    if (validated.sortBy) {
      if (['fecha', 'canal', 'moneda', 'total', 'id'].includes(validated.sortBy)) {
        orderBy[validated.sortBy] = validated.sortOrder || 'asc';
      }
    } else {
      orderBy.id = 'asc';
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
      where: { id },
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
