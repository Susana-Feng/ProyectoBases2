import { OpenAPIHono } from '@hono/zod-openapi';
import { prisma } from '../lib/prisma';
import { productoQuerySchema } from '../validators/query-schemas';
import { listProductosRoute, getProductoRoute } from './productos.openapi';

const productos = new OpenAPIHono();

// GET /productos - List all productos with pagination and filters
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
productos.openapi(listProductosRoute, async (c) => {
  try {
    const query = c.req.query();
    const validated = productoQuerySchema.parse(query);

    // Build where clause for filters
    const where: any = {};
    
    if (validated.nombre) {
      where.nombre = validated.nombreExact === 'true'
        ? { equals: validated.nombre }
        : { contains: validated.nombre, mode: 'insensitive' };
    }
    if (validated.codigoAlt) {
      where.codigo_alt = validated.codigoAltExact === 'true'
        ? { equals: validated.codigoAlt }
        : { contains: validated.codigoAlt, mode: 'insensitive' };
    }
    if (validated.categoria) {
      where.categoria = validated.categoriaExact === 'true'
        ? { equals: validated.categoria }
        : { contains: validated.categoria, mode: 'insensitive' };
    }

    // Build order by
    const orderBy: any = {};
    if (validated.sortBy) {
      if (['nombre', 'codigo_alt', 'categoria', 'id'].includes(validated.sortBy)) {
        orderBy[validated.sortBy] = validated.sortOrder || 'asc';
      }
    } else {
      orderBy.id = 'asc';
    }

    // Calculate pagination
    const skip = (validated.page - 1) * validated.limit;

    // Get total count
    const total = await prisma.producto.count({ where });
    const totalPages = Math.ceil(total / validated.limit);

    // Get paginated data
    const data = await prisma.producto.findMany({
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
    console.error('Error listing productos:', error);
    
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

// GET /productos/:id - Get single producto by ID with optional relations
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
productos.openapi(getProductoRoute, async (c) => {
  try {
    const id = parseInt(c.req.param('id'), 10);
    const include = c.req.query('include');

    if (isNaN(id)) {
      return c.json(
        {
          success: false,
          message: 'Invalid producto ID',
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
    if (includes.includes('ordendetalles')) {
      includeObj.ordenDetalles = true;
    }

    const producto = await prisma.producto.findUnique({
      where: { id },
      include: includeObj,
    });

    if (!producto) {
      return c.json(
        {
          success: false,
          message: 'Producto not found',
        },
        404
      );
    }

    return c.json({
      success: true,
      data: producto,
    });
  } catch (error) {
    console.error('Error getting producto:', error);
    
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

export default productos;
