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

    @Scheduled(cron = "0 0 7 * * ?") // 매일 7시 - CME 일일 정산 후, 아시아 개장 전
    public void scheduleSetInitStructureJob() {
        runJob(setInitStructureJob, "setInitStructureJob");
    }

    @Scheduled(cron = "0 30 7 * * ?") // 매일 7시 30분 - 초기 구조 설정 후 선물 월물 추가
    public void scheduleAddFutureMonthJob() {
        runJob(addFutureMonthJob, "addFutureMonthJob");
    }

    @Scheduled(cron = "0 0 18 * * ?") // 매일 18시 - 아시아 마감 후, 유럽 본격 시작 전
    public void scheduleCollectTypeDataJob() {
        runJob(collectTypeDataJob, "collectTypeDataJob");
    }

    @Scheduled(cron = "0 30 6 * * ?") // 매일 6시 30분 - 미국 마감 후, 아시아 개장 전
    public void scheduleTaskletJob() {
        runJob(taskletJob, "taskletJob");
    }
}
