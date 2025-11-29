const DEFAULT_API_URL = "http://localhost:3003/api/neo4j";

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? DEFAULT_API_URL;
