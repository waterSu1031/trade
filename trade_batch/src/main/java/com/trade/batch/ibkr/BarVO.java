package com.trade.batch.ibkr;

import com.ib.client.Bar;
import com.ib.client.Decimal;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * com.ib.client.Bar → DB insert용, 또는 JSON 직렬화용 변환 객체
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BarVO {
    private String time;
    private double open;
    private double high;
    private double low;
    private double close;
    private double volume;
    private int count;
    private double wap;

    public BarVO(Bar bar) {
        this.time = bar.time();
        this.open = bar.open();
        this.high = bar.high();
        this.low = bar.low();
        this.close = bar.close();
        this.volume = toDouble(bar.volume());
        this.count = bar.count();
        this.wap = toDouble(bar.wap());
    }

    private double toDouble(Decimal d) {
        return (d != null && d.isValid()) ? d.value().doubleValue() : 0.0;
    }
}
