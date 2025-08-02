package com.trade.batch.config;

import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;

@Component
public class JdbcDataSourceRouter {

    public JdbcTemplate getJdbcTemplate(String database) {
        // PostgreSQL 연결 설정
        String url = "jdbc:postgresql://localhost:5432/" + database;
        DataSource ds = DataSourceBuilder.create()
                .driverClassName("org.postgresql.Driver")
                .url(url)
                .username("freeksj")
                .password("Lsld1501!")
                .build();
        return new JdbcTemplate(ds);
    }
}
