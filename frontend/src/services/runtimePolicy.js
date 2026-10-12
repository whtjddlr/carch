export const demoRowsForChannel = (isDemoChannel, rows = []) => (
  isDemoChannel && Array.isArray(rows)
    ? rows.map((row) => ({ ...row }))
    : []
)

export const isUnauthorizedError = (error) => Number(error?.response?.status) === 401
