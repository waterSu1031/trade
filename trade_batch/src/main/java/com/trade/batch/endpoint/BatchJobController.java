package com.trade.batch.endpoint;

import com.trade.batch.job.CollectDataJob;
import lombok.RequiredArgsConstructor;
import org.springframework.batch.core.*;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/batch")
@RequiredArgsConstructor
public class BatchJobController {

    private final JobLauncher jobLauncher;
    private final CollectDataJob collectDataJob;

    @Autowired
    private ApplicationContext context;

    @GetMapping("/run-job/{jobName}")
    public String runJob(@PathVariable String jobName) {
        System.out.println("auto runJob");
        Job job = (Job) context.getBean(jobName);
        return launchJob(job, jobName);
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
