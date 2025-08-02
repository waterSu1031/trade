package com.trade.batch.endpoint;

import com.trade.batch.job.CollectDataJob;
import lombok.RequiredArgsConstructor;
import org.springframework.batch.core.*;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/batch")
@RequiredArgsConstructor
public class BatchJobController {

    private final JobLauncher jobLauncher;
    private final CollectDataJob collectDataJob;

    @Autowired
    private ApplicationContext context;
    
    @Autowired
    private BatchScheduler batchScheduler;

    @GetMapping("/run-job/{jobName}")
    public String runJob(@PathVariable String jobName) {
        System.out.println("auto runJob");
        
        // BatchScheduler의 public 메서드를 직접 호출
        switch (jobName) {
            case "setInitStructureJob":
                batchScheduler.runSetInitStructureJob();
                return "Job 'setInitStructureJob' executed successfully.";
            case "addFutureMonthJob":
                batchScheduler.runAddFutureMonthJob();
                return "Job 'addFutureMonthJob' executed successfully.";
            case "collectTypeDataJob":
                batchScheduler.runCollectTypeDataJob();
                return "Job 'collectTypeDataJob' executed successfully.";
            case "taskletJob":
                batchScheduler.runTaskletJob();
                return "Job 'taskletJob' executed successfully.";
            case "updateWeeklyTradingHours":
                batchScheduler.updateWeeklyTradingHours();
                return "Job 'updateWeeklyTradingHours' executed successfully.";
            default:
                return "Unknown job: " + jobName;
        }
    }

    @GetMapping("/init-structure")
    public String runInitStructureJob() {
        return launchJob(collectDataJob.setInitStructureJob(), "initStructure");
    }

    @PostMapping("/add-future-month")
    public String runAddFutureMonthJob() {
        return launchJob(collectDataJob.addFutureMonthJob(), "addFutureMonth");
    }

    @PostMapping("/collect-type-data")
    public String runCollectTypeDataJob() {
        return launchJob(collectDataJob.collectTypeDataJob(), "collectTypeData");
    }

    @PostMapping("/tasklet")
    public String runTaskletJob() {
        return launchJob(collectDataJob.taskletJob(), "tasklet");
    }

    // 스케줄된 작업 목록 조회
    @GetMapping("/scheduled-jobs")
    public List<Map<String, Object>> getScheduledJobs() {
        List<Map<String, Object>> jobs = new ArrayList<>();
        
        Map<String, Object> job1 = new HashMap<>();
        job1.put("jobName", "setInitStructureJob");
        job1.put("description", "계약 구조 초기화");
        job1.put("cronExpression", "0 0 7 * * ?");
        job1.put("enabled", true);
        jobs.add(job1);
        
        Map<String, Object> job2 = new HashMap<>();
        job2.put("jobName", "addFutureMonthJob");
        job2.put("description", "선물 월물 갱신");
        job2.put("cronExpression", "0 30 7 * * ?");
        job2.put("enabled", true);
        jobs.add(job2);
        
        Map<String, Object> job3 = new HashMap<>();
        job3.put("jobName", "collectTypeDataJob");
        job3.put("description", "시장 데이터 수집");
        job3.put("cronExpression", "0 0 18 * * ?");
        job3.put("enabled", true);
        jobs.add(job3);
        
        Map<String, Object> job4 = new HashMap<>();
        job4.put("jobName", "taskletJob");
        job4.put("description", "배치 작업 처리");
        job4.put("cronExpression", "0 30 6 * * ?");
        job4.put("enabled", true);
        jobs.add(job4);
        
        Map<String, Object> job5 = new HashMap<>();
        job5.put("jobName", "updateWeeklyTradingHours");
        job5.put("description", "거래시간 업데이트");
        job5.put("cronExpression", "0 0 5 * * SUN");
        job5.put("enabled", true);
        jobs.add(job5);
        
        return jobs;
    }
    
    // 거래시간 업데이트
    @PostMapping("/update-trading-hours")
    public Map<String, Object> updateTradingHours() {
        Map<String, Object> result = new HashMap<>();
        try {
            batchScheduler.updateWeeklyTradingHours();
            result.put("status", "success");
            result.put("message", "Trading hours update started successfully");
        } catch (Exception e) {
            result.put("status", "error");
            result.put("message", "Failed to update trading hours: " + e.getMessage());
        }
        return result;
    }

    // 공통 실행 함수
    private String launchJob(Job job, String name) {
        try {
            JobParameters params = new JobParametersBuilder()
                    .addLong("timestamp", System.currentTimeMillis())
                    .addString("jobName", name)
                    .toJobParameters();
            jobLauncher.run(job, params);
            return "Job '" + name + "' executed successfully.";
        } catch (Exception e) {
            return "Error executing job '" + name + "': " + e.getMessage();
        }
    }
}
