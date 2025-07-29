package com.trade.batch.config;

import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;

@Component
public class JdbcDataSourceRouter {

    public JdbcTemplate getJdbcTemplate(String dbFilePath) {
        String url = "jdbc:sqlite:" + dbFilePath;
        DataSource ds = DataSourceBuilder.create()
                .driverClassName("org.postgresql.Driver")
                .url(url)
                .build();
        return new JdbcTemplate(ds);
    }
}
