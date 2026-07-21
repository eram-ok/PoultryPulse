export const productionTrend = [
  { day: "Mon", eggs: 7240, target: 7600 },
  { day: "Tue", eggs: 7580, target: 7600 },
  { day: "Wed", eggs: 7710, target: 7600 },
  { day: "Thu", eggs: 7920, target: 7600 },
  { day: "Fri", eggs: 8060, target: 7600 },
  { day: "Sat", eggs: 8290, target: 7600 },
  { day: "Sun", eggs: 8460, target: 7600 },
]

export const feedStock = [
  { feed: "Layers mash", quantity: 1260, reorder: 600 },
  { feed: "Growers mash", quantity: 740, reorder: 450 },
  { feed: "Chick starter", quantity: 420, reorder: 320 },
  { feed: "Concentrate", quantity: 215, reorder: 180 },
]

export const inventoryBalances = [
  { grade: "Large eggs", quantity: 4320, capacity: 6000 },
  { grade: "Medium eggs", quantity: 2860, capacity: 5000 },
  { grade: "Small eggs", quantity: 940, capacity: 2500 },
  { grade: "Damaged / rejected", quantity: 126, capacity: 800 },
]

export const flockHealth = [
  {
    flock: "Lohmann A-24",
    house: "Layer House 1",
    birds: 4820,
    score: 94,
    status: "Excellent",
  },
  {
    flock: "ISA Brown B-12",
    house: "Layer House 2",
    birds: 3964,
    score: 88,
    status: "Stable",
  },
  {
    flock: "Growers C-07",
    house: "Grower House",
    birds: 900,
    score: 79,
    status: "Watch",
  },
]

export const operationalAlerts = [
  {
    title: "Vaccination due tomorrow",
    detail: "ISA Brown B-12 · Newcastle booster",
    severity: "warning",
    time: "8 min ago",
  },
  {
    title: "Feed stock nearing reorder level",
    detail: "Concentrate is 35 kg above threshold",
    severity: "warning",
    time: "34 min ago",
  },
  {
    title: "Production target exceeded",
    detail: "Sunday collection is 11.3% above target",
    severity: "success",
    time: "1 hr ago",
  },
]

export const recentActivity = [
  {
    event: "Daily production confirmed",
    module: "Production",
    actor: "PoultryPulse Administrator",
    reference: "PRD-2026-0721",
    time: "10:42 PM",
    status: "Confirmed",
  },
  {
    event: "Customer payment recorded",
    module: "Sales",
    actor: "Farm Manager",
    reference: "PAY-000184",
    time: "8:15 PM",
    status: "Completed",
  },
  {
    event: "Feed usage posted",
    module: "Feed",
    actor: "Farm Attendant",
    reference: "FDU-000921",
    time: "5:38 PM",
    status: "Posted",
  },
  {
    event: "Vaccination schedule updated",
    module: "Health",
    actor: "PoultryPulse Administrator",
    reference: "VAC-000067",
    time: "2:05 PM",
    status: "Updated",
  },
]
