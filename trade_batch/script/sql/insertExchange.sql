
-- 거래소 입력
insert into exchange (exchange, sec_type, cnt)
select exchange, 'FUT', count(symbol) cnt from (
	select exchange, symbol, count(exchange)
	from symbol_from_csv sub
	group by exchange, symbol
) T
group by exchange
order by cnt desc
;