import { OpenAPIHono } from '@hono/zod-openapi';
import { prisma } from '../lib/prisma';
import { ordenDetalleQuerySchema } from '../validators/query-schemas';
import { listOrdenDetallesRoute, getOrdenDetalleRoute } from './orden-detalles.openapi';

const ordenDetalles = new OpenAPIHono();

// GET /orden-detalles - List all orden detalles with pagination and filters
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
ordenDetalles.openapi(listOrdenDetallesRoute, async (c) => {
  try {
    const query = c.req.query();
    const validated = ordenDetalleQuerySchema.parse(query);

    // Build where clause for filters
    const where: any = {};
    
    if (validated.ordenId) {
      where.OrdenId = validated.ordenId;
    }
    if (validated.productoId) {
      where.ProductoId = validated.productoId;
    }

    // Build order by
    const orderBy: any = {};
    if (validated.sortBy) {
      if (['Cantidad', 'PrecioUnit', 'DescuentoPct'].includes(validated.sortBy)) {
        orderBy[validated.sortBy] = validated.sortOrder || 'asc';
      }
    } else {
      orderBy.OrdenDetalleId = 'asc';
    }

    // Calculate pagination
    const skip = (validated.page - 1) * validated.limit;

    // Get total count
    const total = await prisma.ordenDetalle.count({ where });
    const totalPages = Math.ceil(total / validated.limit);

    // Get paginated data
    const data = await prisma.ordenDetalle.findMany({
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
    console.error('Error listing orden detalles:', error);
    
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

// GET /orden-detalles/:id - Get single orden detalle by ID with optional relations
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
ordenDetalles.openapi(getOrdenDetalleRoute, async (c) => {
  try {
    const id = parseInt(c.req.param('id'), 10);
    const include = c.req.query('include');

    if (isNaN(id)) {
      return c.json(
        {
          success: false,
          message: 'Invalid orden detalle ID',
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
    if (includes.includes('orden')) {
      includeObj.orden = true;
    }
    if (includes.includes('producto')) {
      includeObj.producto = true;
    }

    const ordenDetalle = await prisma.ordenDetalle.findUnique({
      where: { OrdenDetalleId: id },
      include: includeObj,
    });

    if (!ordenDetalle) {
      return c.json(
        {
          success: false,
          message: 'Orden detalle not found',
        },
        404
      );
    }

    return c.json({
      success: true,
      data: ordenDetalle,
    });
  } catch (error) {
    console.error('Error getting orden detalle:', error);
    
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

export default ordenDetalles;
