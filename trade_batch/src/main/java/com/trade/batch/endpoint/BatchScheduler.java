package com.trade.batch.endpoint;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Component
@Slf4j
@RequiredArgsConstructor
public class BatchScheduler {

    private final JobLauncher jobLauncher;
    private final Job setInitStructureJob;
    private final Job addFutureMonthJob;
    private final Job collectTypeDataJob;
    private final Job taskletJob;

    private void runJob(Job job, String jobName) {
        try {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            log.info("[{}] 실행 시작 - {}", jobName, timestamp);

            JobExecution execution = jobLauncher.run(
                    job, new JobParametersBuilder()
                            .addString("requestTime", timestamp)
                            .toJobParameters()
            );

            log.info("[{}] 실행 종료 - status: {}", jobName, execution.getStatus());
        } catch (Exception e) {
            log.error("[{}] 실행 중 오류 발생: {}", jobName, e.getMessage(), e);
        }
    }

    @Scheduled(cron = "0 0 1 * * ?") // 매일 1시
    public void scheduleSetInitStructureJob() {
        runJob(setInitStructureJob, "setInitStructureJob");
    }

    @Scheduled(cron = "0 0 2 * * ?") // 매일 2시
    public void scheduleAddFutureMonthJob() {
        runJob(addFutureMonthJob, "addFutureMonthJob");
    }

    @Scheduled(cron = "0 0 3 * * ?") // 매일 3시
    public void scheduleCollectTypeDataJob() {
        runJob(collectTypeDataJob, "collectTypeDataJob");
    }

    @Scheduled(cron = "0 0 4 * * ?") // 매일 4시
    public void scheduleTaskletJob() {
        runJob(taskletJob, "taskletJob");
    }
}
