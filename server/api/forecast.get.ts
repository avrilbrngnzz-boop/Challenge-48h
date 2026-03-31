export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const apiBase = process.env.DATA_API_URL || 'http://localhost:8000'

  const params = new URLSearchParams()
  if (query.date)     params.set('date',     query.date     as string)
  if (query.lookback) params.set('lookback', query.lookback as string)
  if (query.horizon)  params.set('horizon',  query.horizon  as string)

  return $fetch(`${apiBase}/forecast?${params}`)
})
