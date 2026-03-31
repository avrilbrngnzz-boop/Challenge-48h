import Database from 'better-sqlite3'
import { resolve } from 'path'

export default defineEventHandler((event) => {
  const query = getQuery(event)

  const startDate = query.startDate as string | undefined
  const endDate   = query.endDate   as string | undefined
  const minIndex  = query.minIndex  !== undefined ? Number(query.minIndex)  : undefined
  const maxIndex  = query.maxIndex  !== undefined ? Number(query.maxIndex)  : undefined
  const minLat    = query.minLat    !== undefined ? Number(query.minLat)    : undefined
  const maxLat    = query.maxLat    !== undefined ? Number(query.maxLat)    : undefined
  const minLon    = query.minLon    !== undefined ? Number(query.minLon)    : undefined
  const maxLon    = query.maxLon    !== undefined ? Number(query.maxLon)    : undefined

  const dbPath = process.env.DB_PATH || resolve(process.cwd(), 'data/pollution.db')

  let db: InstanceType<typeof Database> | null = null

  try {
    db = new Database(dbPath, { readonly: true })
  } catch {
    return []
  }

  let sql = 'SELECT * FROM mesures WHERE 1=1'
  const params: (string | number)[] = []

  if (startDate)             { sql += ' AND date >= ?';   params.push(startDate) }
  if (endDate)               { sql += ' AND date <= ?';   params.push(endDate) }
  if (minIndex !== undefined) { sql += ' AND indice >= ?'; params.push(minIndex) }
  if (maxIndex !== undefined) { sql += ' AND indice <= ?'; params.push(maxIndex) }
  if (minLat   !== undefined) { sql += ' AND lat >= ?';    params.push(minLat) }
  if (maxLat   !== undefined) { sql += ' AND lat <= ?';    params.push(maxLat) }
  if (minLon   !== undefined) { sql += ' AND lon >= ?';    params.push(minLon) }
  if (maxLon   !== undefined) { sql += ' AND lon <= ?';    params.push(maxLon) }

  try {
    const rows = db.prepare(sql).all(...params)
    return rows
  } finally {
    db.close()
  }
})
