const forkliftId = import.meta.env.VITE_FORKLIFT_ID
const warehouseId = import.meta.env.VITE_WAREHOUSE_ID

if (!forkliftId) throw new Error('VITE_FORKLIFT_ID is not set')
if (!warehouseId) throw new Error('VITE_WAREHOUSE_ID is not set')

export const FORKLIFT_ID: string = forkliftId
export const WAREHOUSE_ID: string = warehouseId
