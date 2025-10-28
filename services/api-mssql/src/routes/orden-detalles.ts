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
    
    // Cantidad numeric filters
    if (validated.cantidadMin || validated.cantidadMax || validated.cantidadGt || validated.cantidadLt || validated.cantidadEq) {
      where.Cantidad = {};
      if (validated.cantidadMin) {
        where.Cantidad.gte = validated.cantidadMin;
      }
      if (validated.cantidadMax) {
        where.Cantidad.lte = validated.cantidadMax;
      }
      if (validated.cantidadGt) {
        where.Cantidad.gt = validated.cantidadGt;
      }
      if (validated.cantidadLt) {
        where.Cantidad.lt = validated.cantidadLt;
      }
      if (validated.cantidadEq) {
        where.Cantidad.equals = validated.cantidadEq;
      }
    }
    
    // PrecioUnit numeric filters
    if (validated.precioUnitMin || validated.precioUnitMax || validated.precioUnitGt || validated.precioUnitLt || validated.precioUnitEq) {
      where.PrecioUnit = {};
      if (validated.precioUnitMin) {
        where.PrecioUnit.gte = validated.precioUnitMin;
      }
      if (validated.precioUnitMax) {
        where.PrecioUnit.lte = validated.precioUnitMax;
      }
      if (validated.precioUnitGt) {
        where.PrecioUnit.gt = validated.precioUnitGt;
      }
      if (validated.precioUnitLt) {
        where.PrecioUnit.lt = validated.precioUnitLt;
      }
      if (validated.precioUnitEq) {
        where.PrecioUnit.equals = validated.precioUnitEq;
      }
    }
    
    // DescuentoPct numeric filters
    if (validated.descuentoMin || validated.descuentoMax || validated.descuentoGt || validated.descuentoLt || validated.descuentoEq) {
      where.DescuentoPct = {};
      if (validated.descuentoMin) {
        where.DescuentoPct.gte = validated.descuentoMin;
      }
      if (validated.descuentoMax) {
        where.DescuentoPct.lte = validated.descuentoMax;
      }
      if (validated.descuentoGt) {
        where.DescuentoPct.gt = validated.descuentoGt;
      }
      if (validated.descuentoLt) {
        where.DescuentoPct.lt = validated.descuentoLt;
      }
      if (validated.descuentoEq) {
        where.DescuentoPct.equals = validated.descuentoEq;
      }
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
