"""
equivalences.py
Build product equivalence map from all sources BEFORE transformation.

This module solves the problem of mapping products across heterogeneous sources:
- MSSQL has SKU (official)
- MySQL has codigo_alt
- Supabase has SKU (may be empty)
- MongoDB has codigo_mongo + equivalencias.sku + equivalencias.codigo_alt
- Neo4j has sku + codigo_alt + codigo_mongo

The equivalence map is built by:
1. Grouping products by (nombre, categoria) across all sources
2. For each group, finding the best SKU using priority order
3. Generating a new SKU only if no source has one

Priority for SKU resolution:
1. MSSQL SKU (canonical source)
2. Supabase SKU (if not empty)
3. MongoDB equivalencias.sku
4. Neo4j sku
5. Generate new SKU
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ProductInfo:
    """Information about a product from a specific source."""
    source: str
    source_code: str  # The code used by this source (SKU, codigo_alt, codigo_mongo, etc.)
    sku: Optional[str] = None  # SKU if available
    nombre: str = ""
    categoria: str = ""
    es_servicio: bool = False


@dataclass
class ProductEquivalence:
    """Equivalence information for a product across all sources."""
    nombre: str
    categoria: str
    sku_oficial: str  # The canonical SKU to use
    es_servicio: bool = False
    sources: Dict[str, ProductInfo] = field(default_factory=dict)
    
    def get_source_code(self, source: str) -> Optional[str]:
        """Get the source_code for a specific source."""
        if source in self.sources:
            return self.sources[source].source_code
        return None


class EquivalenceMap:
    """
    Map of product equivalences across all sources.
    
    Usage:
        eq_map = EquivalenceMap()
        eq_map.add_mssql_products(productos_mssql)
        eq_map.add_mysql_products(productos_mysql)
        ...
        eq_map.resolve_skus()  # Assign SKUs to all products
        
        # During transformation:
        sku = eq_map.get_sku("mysql", "ALT-AB12")
        # or
        sku = eq_map.get_sku_by_name("Televisor LED 32", "Electrónica")
    """
    
    def __init__(self):
        # Map: (nombre_lower, categoria_lower) -> ProductEquivalence
        self._by_name_cat: Dict[tuple, ProductEquivalence] = {}
        # Map: (source, source_code) -> ProductEquivalence
        self._by_source_code: Dict[tuple, ProductEquivalence] = {}
        # Counter for generating new SKUs
        self._next_sku_num = 1
        # Track if SKUs have been resolved
        self._resolved = False
    
    def _normalize_key(self, nombre: str, categoria: str) -> tuple:
        """Create a normalized key for name+category lookup."""
        return (
            (nombre or "").strip().lower(),
            (categoria or "").strip().lower()
        )
    
    def _get_or_create_equivalence(self, nombre: str, categoria: str) -> ProductEquivalence:
        """Get existing equivalence or create new one."""
        key = self._normalize_key(nombre, categoria)
        if key not in self._by_name_cat:
            self._by_name_cat[key] = ProductEquivalence(
                nombre=nombre,
                categoria=categoria,
                sku_oficial=""  # Will be resolved later
            )
        return self._by_name_cat[key]
    
    def _add_product(self, info: ProductInfo):
        """Add a product to the equivalence map."""
        eq = self._get_or_create_equivalence(info.nombre, info.categoria)
        eq.sources[info.source] = info
        
        # Also index by source_code for fast lookup during transformation
        source_key = (info.source, info.source_code)
        self._by_source_code[source_key] = eq
        
        # Track if it's a service
        if info.es_servicio:
            eq.es_servicio = True
    
    def add_mssql_products(self, productos: List[Any], debug: bool = False):
        """
        Add products from MSSQL extraction.
        MSSQL has: ProductoId, SKU, Nombre, Categoria
        """
        for i, p in enumerate(productos):
            # MSSQL returns Row objects with capitalized column names
            sku = getattr(p, 'SKU', None)
            nombre = getattr(p, 'Nombre', None) or ''
            categoria = getattr(p, 'Categoria', None) or ''
            producto_id = getattr(p, 'ProductoId', '')
            
            if debug and i < 3:
                print(f"        MSSQL sample {i}: SKU={sku}, nombre={nombre[:30] if nombre else 'EMPTY'}, cat={categoria}")
            
            info = ProductInfo(
                source="mssql",
                source_code=str(producto_id),
                sku=sku,
                nombre=nombre,
                categoria=categoria,
            )
            self._add_product(info)
    
    def add_mysql_products(self, productos: List[Any], debug: bool = False):
        """
        Add products from MySQL extraction.
        MySQL has: id, codigo_alt, nombre, categoria (lowercase columns)
        """
        for i, p in enumerate(productos):
            # MySQL returns Row objects with lowercase column names
            codigo_alt = getattr(p, 'codigo_alt', None) or ''
            nombre = getattr(p, 'nombre', None) or ''
            categoria = getattr(p, 'categoria', None) or ''
            
            if debug and i < 3:
                print(f"        MySQL sample {i}: codigo_alt={codigo_alt}, nombre={nombre[:30] if nombre else 'EMPTY'}, cat={categoria}")
            
            info = ProductInfo(
                source="mysql",
                source_code=codigo_alt,
                sku=None,  # MySQL doesn't have SKU
                nombre=nombre,
                categoria=categoria,
            )
            self._add_product(info)
    
    def add_supabase_products(self, productos: List[Dict[str, Any]], debug: bool = False):
        """
        Add products from Supabase extraction.
        Supabase has: producto_id, sku (may be empty), nombre, categoria
        """
        for i, p in enumerate(productos):
            sku = p.get('sku') or None
            producto_id = p.get('producto_id', '')
            nombre = p.get('nombre', '')
            categoria = p.get('categoria', '')
            
            if debug and i < 3:
                print(f"        Supabase sample {i}: sku={sku}, nombre={nombre[:30] if nombre else 'EMPTY'}, cat={categoria}")
            
            # Use SKU as source_code if available, otherwise use producto_id
            source_code = sku if sku else str(producto_id)
            
            info = ProductInfo(
                source="supabase",
                source_code=source_code,
                sku=sku if sku else None,  # Only set if not empty
                nombre=nombre,
                categoria=categoria,
                es_servicio=False,
            )
            self._add_product(info)
    
    def add_mongo_products(self, productos: List[Dict[str, Any]], debug: bool = False):
        """
        Add products from MongoDB extraction.
        MongoDB has: codigo_mongo, nombre, categoria, equivalencias: {sku, codigo_alt}
        """
        for i, p in enumerate(productos):
            codigo_mongo = p.get('codigo_mongo', '')
            nombre = p.get('nombre', '')
            categoria = p.get('categoria', '')
            equivalencias = p.get('equivalencias', {}) or {}
            sku_equiv = equivalencias.get('sku')
            
            if debug and i < 3:
                print(f"        MongoDB sample {i}: codigo_mongo={codigo_mongo}, nombre={nombre[:30] if nombre else 'EMPTY'}, cat={categoria}")
            
            # Normalize SKU format if present
            if sku_equiv:
                sku_equiv = self._normalize_sku(sku_equiv)
            
            info = ProductInfo(
                source="mongo",
                source_code=codigo_mongo,
                sku=sku_equiv,
                nombre=nombre,
                categoria=categoria,
            )
            self._add_product(info)
    
    def add_neo4j_products(self, productos: List[Dict[str, Any]], debug: bool = False):
        """
        Add products from Neo4j extraction.
        Neo4j has: id/sku, nombre, categoria, codigo_alt, codigo_mongo
        """
        for i, p in enumerate(productos):
            sku = p.get('sku') or p.get('id')
            nombre = p.get('nombre', '')
            categoria = p.get('categoria', '')
            
            if debug and i < 3:
                print(f"        Neo4j sample {i}: sku={sku}, nombre={nombre[:30] if nombre else 'EMPTY'}, cat={categoria}")
            
            # Normalize SKU format if present
            if sku:
                sku = self._normalize_sku(sku)
            
            info = ProductInfo(
                source="neo4j",
                source_code=sku or '',
                sku=sku,
                nombre=nombre,
                categoria=categoria,
            )
            self._add_product(info)
    
    def _normalize_sku(self, sku: str) -> str:
        """Normalize SKU to format SKU-XXXX."""
        if not sku:
            return sku
        sku = sku.strip()
        # Convert SKU0001 to SKU-0001
        if sku.upper().startswith("SKU") and "-" not in sku and len(sku) > 3:
            return f"SKU-{sku[3:]}"
        return sku
    
    def _generate_sku(self) -> str:
        """Generate a new unique SKU."""
        sku = f"SKU-{self._next_sku_num:04d}"
        self._next_sku_num += 1
        return sku
    
    def resolve_skus(self, existing_max_sku: int = 0):
        """
        Resolve SKUs for all products using priority order.
        
        Args:
            existing_max_sku: The highest SKU number already in the database.
                              New SKUs will start from this + 1.
        
        Priority:
        1. MSSQL SKU (canonical)
        2. Supabase SKU (if not empty)
        3. MongoDB equivalencias.sku
        4. Neo4j sku
        5. Generate new SKU
        """
        if existing_max_sku > 0:
            self._next_sku_num = existing_max_sku + 1
        
        # First pass: collect all existing SKUs to avoid duplicates
        existing_skus = set()
        for eq in self._by_name_cat.values():
            for source in ["mssql", "supabase", "mongo", "neo4j"]:
                if source in eq.sources and eq.sources[source].sku:
                    existing_skus.add(eq.sources[source].sku)
        
        # Second pass: resolve SKUs
        for eq in self._by_name_cat.values():
            sku = None
            
            # Priority 1: MSSQL
            if "mssql" in eq.sources and eq.sources["mssql"].sku:
                sku = eq.sources["mssql"].sku
            
            # Priority 2: Supabase
            if not sku and "supabase" in eq.sources and eq.sources["supabase"].sku:
                sku = eq.sources["supabase"].sku
            
            # Priority 3: MongoDB equivalencias.sku
            if not sku and "mongo" in eq.sources and eq.sources["mongo"].sku:
                sku = eq.sources["mongo"].sku
            
            # Priority 4: Neo4j sku
            if not sku and "neo4j" in eq.sources and eq.sources["neo4j"].sku:
                sku = eq.sources["neo4j"].sku
            
            # Priority 5: Generate new SKU
            if not sku:
                # Generate SKU that doesn't conflict with existing ones
                while True:
                    sku = self._generate_sku()
                    if sku not in existing_skus:
                        break
            
            eq.sku_oficial = sku
            existing_skus.add(sku)
        
        self._resolved = True
        return self
    
    def get_sku(self, source: str, source_code: str) -> Optional[str]:
        """
        Get the canonical SKU for a product by source and source_code.
        
        Args:
            source: The source system ('mssql', 'mysql', 'supabase', 'mongo', 'neo4j')
            source_code: The product code in that source
        
        Returns:
            The canonical SKU, or None if not found
        """
        if not self._resolved:
            raise RuntimeError("Must call resolve_skus() before get_sku()")
        
        key = (source, source_code)
        if key in self._by_source_code:
            return self._by_source_code[key].sku_oficial
        return None
    
    def get_sku_by_name(self, nombre: str, categoria: str) -> Optional[str]:
        """
        Get the canonical SKU for a product by name and category.
        
        Args:
            nombre: Product name
            categoria: Product category
        
        Returns:
            The canonical SKU, or None if not found
        """
        if not self._resolved:
            raise RuntimeError("Must call resolve_skus() before get_sku_by_name()")
        
        key = self._normalize_key(nombre, categoria)
        if key in self._by_name_cat:
            return self._by_name_cat[key].sku_oficial
        return None
    
    def get_equivalence(self, nombre: str, categoria: str) -> Optional[ProductEquivalence]:
        """Get the full equivalence information for a product."""
        key = self._normalize_key(nombre, categoria)
        return self._by_name_cat.get(key)
    
    def get_equivalence_by_source(self, source: str, source_code: str) -> Optional[ProductEquivalence]:
        """Get the full equivalence information for a product by source code."""
        key = (source, source_code)
        return self._by_source_code.get(key)
    
    def is_service(self, source: str, source_code: str) -> bool:
        """Check if a product is a service (no physical SKU)."""
        key = (source, source_code)
        if key in self._by_source_code:
            return self._by_source_code[key].es_servicio
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the equivalence map."""
        total_products = len(self._by_name_cat)
        by_source = {
            "mssql": 0,
            "mysql": 0,
            "supabase": 0,
            "mongo": 0,
            "neo4j": 0,
        }
        services = 0
        sku_from = {
            "mssql": 0,
            "supabase": 0,
            "mongo": 0,
            "neo4j": 0,
            "generated": 0,
        }
        
        for eq in self._by_name_cat.values():
            for source in eq.sources:
                by_source[source] = by_source.get(source, 0) + 1
            
            if eq.es_servicio:
                services += 1
            
            # Track where the SKU came from
            if "mssql" in eq.sources and eq.sources["mssql"].sku == eq.sku_oficial:
                sku_from["mssql"] += 1
            elif "supabase" in eq.sources and eq.sources["supabase"].sku == eq.sku_oficial:
                sku_from["supabase"] += 1
            elif "mongo" in eq.sources and eq.sources["mongo"].sku == eq.sku_oficial:
                sku_from["mongo"] += 1
            elif "neo4j" in eq.sources and eq.sources["neo4j"].sku == eq.sku_oficial:
                sku_from["neo4j"] += 1
            else:
                sku_from["generated"] += 1
        
        return {
            "total_products": total_products,
            "by_source": by_source,
            "services": services,
            "sku_from": sku_from,
        }
    
    def __len__(self) -> int:
        return len(self._by_name_cat)
    
    def __iter__(self):
        return iter(self._by_name_cat.values())


def build_equivalence_map(
    productos_mssql: List[Any] = None,
    productos_mysql: List[Any] = None,
    productos_supabase: List[Dict] = None,
    productos_mongo: List[Dict] = None,
    productos_neo4j: List[Dict] = None,
    existing_max_sku: int = 0,
    debug: bool = False,
) -> EquivalenceMap:
    """
    Build an equivalence map from all extracted products.
    
    This should be called after extraction and before transformation.
    
    Args:
        productos_mssql: Products from MSSQL extraction
        productos_mysql: Products from MySQL extraction
        productos_supabase: Products from Supabase extraction
        productos_mongo: Products from MongoDB extraction
        productos_neo4j: Products from Neo4j extraction
        existing_max_sku: Highest SKU number already in database
        debug: Print debug information
    
    Returns:
        EquivalenceMap with all products and resolved SKUs
    """
    eq_map = EquivalenceMap()
    
    before = len(eq_map)
    if productos_mssql:
        eq_map.add_mssql_products(productos_mssql, debug=debug)
        if debug:
            print(f"      MSSQL: added {len(productos_mssql)} products, unique now: {len(eq_map)} (+{len(eq_map) - before})")
        before = len(eq_map)
    
    if productos_mysql:
        eq_map.add_mysql_products(productos_mysql, debug=debug)
        if debug:
            print(f"      MySQL: added {len(productos_mysql)} products, unique now: {len(eq_map)} (+{len(eq_map) - before})")
        before = len(eq_map)
    
    if productos_supabase:
        eq_map.add_supabase_products(productos_supabase, debug=debug)
        if debug:
            print(f"      Supabase: added {len(productos_supabase)} products, unique now: {len(eq_map)} (+{len(eq_map) - before})")
        before = len(eq_map)
    
    if productos_mongo:
        eq_map.add_mongo_products(productos_mongo, debug=debug)
        if debug:
            print(f"      MongoDB: added {len(productos_mongo)} products, unique now: {len(eq_map)} (+{len(eq_map) - before})")
        before = len(eq_map)
    
    if productos_neo4j:
        eq_map.add_neo4j_products(productos_neo4j, debug=debug)
        if debug:
            print(f"      Neo4j: added {len(productos_neo4j)} products, unique now: {len(eq_map)} (+{len(eq_map) - before})")
    
    eq_map.resolve_skus(existing_max_sku)
    
    return eq_map

