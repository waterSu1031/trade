package com.trade.batch;

//import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.WebApplicationType;
import org.springframework.scheduling.annotation.EnableScheduling;


@SpringBootApplication
@EnableScheduling
public class BatchApplication {
	public static void main(String[] args) {
//		SpringApplication.run(BatchApplication.class, args);

		// CLI 매개변수로 잡명 지정 등 유연하게 처리
		new SpringApplicationBuilder(BatchApplication.class)
				.web(WebApplicationType.SERVLET) // Web서버 비활성화 (배치 전용)
				.run(args); // test
	}
}
