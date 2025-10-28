import { OpenAPIHono } from '@hono/zod-openapi';
import { prisma } from '../lib/prisma';
import { clienteQuerySchema, type ClienteQuery } from '../validators/query-schemas';
import { listClientesRoute, getClienteRoute } from './clientes.openapi';

const clientes = new OpenAPIHono();

// GET /clientes - List all clientes with pagination and filters
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
clientes.openapi(listClientesRoute, async (c) => {
  try {
    const query = c.req.query();
    const validated = clienteQuerySchema.parse(query);

    // Build where clause for filters
    const where: any = {};
    
    if (validated.nombre) {
      where.Nombre = { contains: validated.nombre };
    }
    if (validated.email) {
      where.Email = { contains: validated.email };
    }
    if (validated.pais) {
      where.Pais = { contains: validated.pais };
    }
    if (validated.genero) {
      where.Genero = { contains: validated.genero };
    }

    // Build order by
    const orderBy: any = {};
    if (validated.sortBy) {
      const field = validated.sortBy as keyof typeof where;
      if (['Nombre', 'Email', 'Pais', 'Genero', 'FechaRegistro'].includes(validated.sortBy)) {
        orderBy[field] = validated.sortOrder || 'asc';
      }
    } else {
      orderBy.ClienteId = 'asc';
    }

    // Calculate pagination
    const skip = (validated.page - 1) * validated.limit;

    // Get total count
    const total = await prisma.cliente.count({ where });
    const totalPages = Math.ceil(total / validated.limit);

    // Get paginated data
    const data = await prisma.cliente.findMany({
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
    console.error('Error listing clientes:', error);
    
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

// GET /clientes/:id - Get single cliente by ID with optional relations
// @ts-expect-error - Hono OpenAPI type inference issue with multiple response types
clientes.openapi(getClienteRoute, async (c) => {
  try {
    const id = parseInt(c.req.param('id'), 10);
    const include = c.req.query('include');

    if (isNaN(id)) {
      return c.json(
        {
          success: false,
          message: 'Invalid cliente ID',
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
    if (includes.includes('ordenes')) {
      includeObj.ordenes = true;
    }

    const cliente = await prisma.cliente.findUnique({
      where: { ClienteId: id },
      include: includeObj,
    });

    if (!cliente) {
      return c.json(
        {
          success: false,
          message: 'Cliente not found',
        },
        404
      );
    }

    return c.json({
      success: true,
      data: cliente,
    });
  } catch (error) {
    console.error('Error getting cliente:', error);
    
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

export default clientes;
