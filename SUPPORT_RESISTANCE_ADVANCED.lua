-- SUPPORT_RESISTANCE_ADVANCED.lua

-- Define colors for support and resistance zones
local supportColor = Color.red
local resistanceColor = Color.green

-- Define zone strength as a parameter
local zoneStrength = {weak = 0.3, medium = 0.5, strong = 0.8}

-- Function to draw support zones
function drawSupportZone(value, strength)
    local opacity = zoneStrength[strength]
    if opacity then
        line(value, 0, value, screenHeight, supportColor.withAlpha(opacity))
    end
end

-- Function to draw resistance zones
function drawResistanceZone(value, strength)
    local opacity = zoneStrength[strength]
    if opacity then
        line(value, 0, value, screenHeight, resistanceColor.withAlpha(opacity))
    end
end

-- Function to draw buy entry arrows
function drawBuyArrow(price)
    arrow(price, 0, 'up', Color.yellow)
end

-- Function to draw sell entry arrows
function drawSellArrow(price)
    arrow(price, 0, 'down', Color.orange)
end

-- Example usage
-- Draw support zones
for i, zone in pairs(supportZones) do
    drawSupportZone(zone.price, zone.strength)
end

-- Draw resistance zones
for i, zone in pairs(resistanceZones) do
    drawResistanceZone(zone.price, zone.strength)
end

-- Check for breakouts and draw arrows
if breakout.support then
    drawBuyArrow(currentPrice)
end
if breakout.resistance then
    drawSellArrow(currentPrice)
end

-- Zone entry indicators
for i, zone in pairs(entryIndicators) do
    displayIndicator(zone.price, zone.type)
end

-- Enable all filters
setFilter('all', true)