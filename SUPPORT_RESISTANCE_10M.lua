instrument {
    name = 'SUPPORT & RESISTANCE ZONES',
    short_name = 'SR-ZONES-10M',
    overlay = true
}

zone_lookback = input(50, "Zone Lookback Period", input.integer, 10, 200, 5)
zone_tolerance = input(0.5, "Zone Tolerance %", input.double, 0.1, 2.0, 0.1, true)
min_touches = input(3, "Minimum Zone Touches", input.integer, 2, 10, 1)
breakout_confirm = input(2, "Breakout Confirmation Bars", input.integer, 1, 5, 1)

timeframe_options = {"10m", "15m", "30m", "1H", "2H", "4H"}
timeframe_index = input(1, "Chart Timeframe", input.string_selection, timeframe_options)

use_volume_filter = input(true, "Use Volume Filter", input.bool)
volume_multiplier = input(1.5, "Volume Multiplier", input.double, 1.0, 3.0, 0.1, true)
use_rsi_filter = input(true, "Use RSI Filter", input.bool)
rsi_period = input(14, "RSI Period", input.integer, 5, 50, 1)

input_group {
    "Support Zone Settings",
    colorSupport = input { default = "lime", type = input.color },
    widthSupport = input { default = 2, type = input.line_width },
    visibleSupport = input { default = true, type = input.plot_visibility }
}

input_group {
    "Resistance Zone Settings",
    colorResistance = input { default = "red", type = input.color },
    widthResistance = input { default = 2, type = input.line_width },
    visibleResistance = input { default = true, type = input.plot_visibility }
}

input_group {
    "Buy Signal - Support Breakout",
    colorBuy = input { default = "white", type = input.color },
    visibleBuy = input { default = true, type = input.plot_visibility }
}

input_group {
    "Sell Signal - Resistance Breakout",
    colorSell = input { default = "yellow", type = input.color },
    visibleSell = input { default = true, type = input.plot_visibility }
}

input_group {
    "Zone Touch Alerts",
    colorTouch = input { default = "orange", type = input.color },
    visibleTouch = input { default = true, type = input.plot_visibility }
}

rsi_average = averages[2]
rsi_title = inputs[1]

delta = rsi_title - rsi_title[1]
up = rsi_average(max(delta, 0), rsi_period)
down = rsi_average(max(-delta, 0), rsi_period)
RS = up / down

rsi_value = 100 - 100 / (1 + RS)

sec = security(current_ticker_id, timeframe_options[timeframe_index])

if (sec ~= nil) then

    support_level = low
    for i = 1, zone_lookback do
        if low[i] < support_level then
            support_level = low[i]
        end
    end

    resistance_level = high
    for i = 1, zone_lookback do
        if high[i] > resistance_level then
            resistance_level = high[i]
        end
    end

    zone_range = resistance_level - support_level
    zone_tol = zone_range * (zone_tolerance / 100)

    support_touches = 0
    for i = 1, zone_lookback do
        if (low[i] >= (support_level - zone_tol) and low[i] <= (support_level + zone_tol)) or
           (close[i] >= (support_level - zone_tol) and close[i] <= (support_level + zone_tol)) then
            support_touches = support_touches + 1
        end
    end

    resistance_touches = 0
    for i = 1, zone_lookback do
        if (high[i] >= (resistance_level - zone_tol) and high[i] <= (resistance_level + zone_tol)) or
           (close[i] >= (resistance_level - zone_tol) and close[i] <= (resistance_level + zone_tol)) then
            resistance_touches = resistance_touches + 1
        end
    end

    if visibleSupport == true then
        if support_touches >= min_touches then
            plot(support_level, "Support Zone", colorSupport, widthSupport)
        end
    end

    if visibleResistance == true then
        if resistance_touches >= min_touches then
            plot(resistance_level, "Resistance Zone", colorResistance, widthResistance)
        end
    end

    if visibleTouch == true then
        if (low >= (support_level - zone_tol) and low <= (support_level + zone_tol)) and support_touches >= min_touches then
            plot_shape(true,
                "Support Touch",
                shape_style.circle,
                shape_size.small,
                colorTouch,
                shape_location.belowbar,
                0,
                "ZONE TOUCH",
                colorTouch
            )
        end
    end

    if visibleTouch == true then
        if (high >= (resistance_level - zone_tol) and high <= (resistance_level + zone_tol)) and resistance_touches >= min_touches then
            plot_shape(true,
                "Resistance Touch",
                shape_style.circle,
                shape_size.small,
                colorTouch,
                shape_location.abovebar,
                0,
                "ZONE TOUCH",
                colorTouch
            )
        end
    end

    if visibleBuy == true then

        breakout_up = close > (support_level + zone_tol) and close[1] <= (support_level + zone_tol)

        confirm_up = true
        for i = 1, breakout_confirm do
            if close[i] <= (support_level + zone_tol) then
                confirm_up = false
                break
            end
        end

        buy_signal = breakout_up and confirm_up and support_touches >= min_touches

        if use_volume_filter == true then
            buy_signal = buy_signal and volume > volume[1] * volume_multiplier
        end

        if use_rsi_filter == true then
            buy_signal = buy_signal and rsi_value < 70
        end

        if buy_signal == true then
            plot_shape(true,
                "BUY-BREAKOUT",
                shape_style.triangleup,
                shape_size.huge,
                colorBuy,
                shape_location.belowbar,
                0,
                "SUPPORT BREAKOUT",
                colorBuy
            )
        end
    end

    if visibleSell == true then

        breakout_down = close < (resistance_level - zone_tol) and close[1] >= (resistance_level - zone_tol)

        confirm_down = true
        for i = 1, breakout_confirm do
            if close[i] >= (resistance_level - zone_tol) then
                confirm_down = false
                break
            end
        end

        sell_signal = breakout_down and confirm_down and resistance_touches >= min_touches

        if use_volume_filter == true then
            sell_signal = sell_signal and volume > volume[1] * volume_multiplier
        end

        if use_rsi_filter == true then
            sell_signal = sell_signal and rsi_value > 30
        end

        if sell_signal == true then
            plot_shape(true,
                "SELL-BREAKOUT",
                shape_style.triangledown,
                shape_size.huge,
                colorSell,
                shape_location.abovebar,
                0,
                "RESISTANCE BREAKOUT",
                colorSell
            )
        end
    end

end