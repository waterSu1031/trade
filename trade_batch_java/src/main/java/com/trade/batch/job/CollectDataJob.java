package com.trade.batch.job;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ib.client.Bar;
import com.trade.batch.service.CollectDataService;
import com.trade.batch.service.CommonService;
import lombok.RequiredArgsConstructor;
import org.springframework.batch.core.*;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.support.ListItemReader;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.transaction.PlatformTransactionManager;

import java.util.List;
import java.util.Map;

@Configuration
@RequiredArgsConstructor
public class CollectDataJob {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final CollectDataService collectDataService;
    private final CommonService commonService;

    @Bean
    public Job setInitStructureJob() {
        return new JobBuilder("setInitStructureJob", jobRepository)
                .start(initContractDataStep())
                .build();
    }

    @Bean
    public Step initContractDataStep() {
        return new StepBuilder("initContractDataStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(6, transactionManager)
                .reader(initContractDataReader())
                .processor(initContractDataProcessor())
                .writer(initContractDataWriter())
                .build();
    }

    @Bean
    public ItemReader<Map<String, Object>> initContractDataReader() {
        List<Map<String, Object>> symbols = collectDataService.loadSymbolFromAddCSV();
        return new ListItemReader<>(symbols);
    }

    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> initContractDataProcessor() {
        return symbol -> {
            Map<String, Object> contract = collectDataService.fetchContractDetail(symbol);
            return contract;
        };
    }

    @Bean
    public ItemWriter<Map<String, Object>> initContractDataWriter() {
        return contracts -> {
            for (Map<String, Object> contract : contracts) {
                collectDataService.saveContractRel(contract);
            }
            Thread.sleep(10000);
        };
    }

    // --------------------------------------------------------------------------------------

    @Bean
    public Job addFutureMonthJob() {
        return new JobBuilder("addFutureMonthJob", jobRepository)
                .start(addFutureMonthStep())
                .build();
    }

    @Bean
    public Step addFutureMonthStep() {
        return new StepBuilder("addFutureMonthStep", jobRepository)
                .<Map<String, Object>, Map<String, Object>>chunk(6, transactionManager)
                .reader(addFutureMonthReader())
                .processor(addFutureMonthProcessor())
                .writer(addFutureMonthWriter())
                .listener(addFutureMonthListener())
                .build();
    }

    @Bean
    public ItemReader<Map<String, Object>> addFutureMonthReader() {
        List<Map<String, Object>> contracts = collectDataService.loadTargetFutureContracts();
        return new ListItemReader<>(contracts);
    }

    @Bean
    public ItemProcessor<Map<String, Object>, Map<String, Object>> addFutureMonthProcessor() {
        return contract -> {
            Map<String, Object> futureMonth = collectDataService.collectFutureMonth(contract);
            return futureMonth;
        };
    }

    @Bean
    public ItemWriter<Map<String, Object>> addFutureMonthWriter() {
        return months -> {
            for (Map<String, Object> month : months) {
                collectDataService.saveFutureMonths(month);
            }
            Thread.sleep(10000);
        };
    }

    @Bean
    public StepExecutionListener addFutureMonthListener() {
        return new StepExecutionListener() {
            @Override
            public void beforeStep(@NonNull StepExecution stepExecution) {
                System.out.println("🔹 [addFutureMonth] 시작");
            }
            @Override
            public ExitStatus afterStep(@NonNull StepExecution stepExecution) {
                System.out.println("🔸 [addFutureMonth] 종료" + stepExecution.getStatus());
                return stepExecution.getExitStatus(); // ★ 반드시 ExitStatus 반환!
            }
        };
    }

    // --------------------------------------------------------------------------------------

    @Bean
    public Job collectTypeDataJob() {
        return new JobBuilder("collectTypeDataJob", jobRepository)
                .start(collectTimeDataStep())
                .next(convertRangeDataStep())
                .build();
    }

    @Bean
    public Step collectTimeDataStep() {
        return new StepBuilder("collectTimeDataStep", jobRepository)
                .<Map<String, Object>, List<Map<String, Object>>>chunk(6, transactionManager)
                .reader(collectTimeDataReader())
                .processor(collectTimeDataProcessor())
                .writer(collectTimeDataWriter())
                .build();
    }

    @Bean
    public ItemReader<Map<String, Object>> collectTimeDataReader() {
        List<Map<String, Object>> contracts = collectDataService.loadContractForCollectTime();
        return new ListItemReader<>(contracts);
    }

    @Bean
    public ItemProcessor<Map<String, Object>, List<Map<String, Object>>> collectTimeDataProcessor(){
        return contract -> {
            List<Map<String, Object>> times = collectDataService.collectTimeData(contract);
            return times;
        };
    }

    @Bean
    public ItemWriter<List<Map<String, Object>>> collectTimeDataWriter() {
         return times -> {
            for (List<Map<String, Object>> bars : times) {
                for (Map<String, Object> bar : bars) {
                    collectDataService.saveTimeData(bar);
                }
            }
        };
    }

    @Bean
    public Step convertRangeDataStep() {
        return new StepBuilder("convertRangeDataStep", jobRepository)
                .<Map<String, Object>, List<Map<String, Object>>>chunk(10, transactionManager)
                .reader(convertRangeDataReader())
                .processor(convertRangeDataProcessor())
                .writer(convertRangeDataWriter())
                .build();
    }

    @Bean
    public ItemReader<Map<String, Object>> convertRangeDataReader() {
        List<Map<String, Object>> contracts = collectDataService.loadContractForConvertRange();
        return new ListItemReader<>(contracts);
    }

    @Bean
    public ItemProcessor<Map<String, Object>, List<Map<String, Object>>> convertRangeDataProcessor() {
        return contract -> {
//            List<Bar> ranges = new ObjectMapper().convertValue(contract, new TypeReference<List<Bar>>() {});
            List<Map<String, Object>> ranges = collectDataService.convertTimetoRange(contract);
            return ranges;
        };
    }

    @Bean
    public ItemWriter<List<Map<String, Object>>> convertRangeDataWriter() {
        return ranges -> {
            for (List<Map<String, Object>> bars : ranges) {
                for (Map<String, Object> bar : bars) {
                    collectDataService.saveRangeData(bar);
                }
            }
        };
    }

    //    ----------------------------------------------------------------------------------------

    @Bean
    public Job taskletJob() {
        return new JobBuilder("sampleTaskletJob", jobRepository)
                .start(taskletStep())
                .listener(taskletJobListener())
                .build();
    }

    @Bean
    public Step taskletStep() {
        return new StepBuilder("taskletStep", jobRepository)
                .tasklet(tasklet(), transactionManager)
//                .tasklet((contribution, chunkContext) -> {
//                    System.out.println("✅ Tasklet 실행 중: 단일 처리 작업 수행");
//                    return RepeatStatus.FINISHED;
//                }, transactionManager)
                .build();
    }

    @Bean
    @StepScope
    public Tasklet tasklet() {
        return (contribution, chunkContext) -> {
            System.out.println("[Tasklet] IBKR Futures 작업 실행 중...");
            return RepeatStatus.FINISHED;
        };
    }

    @Bean
    public JobExecutionListener taskletJobListener() {
        return new JobExecutionListener() {
            public void beforeJob(@NonNull JobExecution jobExecution) {
                System.out.println("🔹 [Tasklet Job] 시작");
            }
            public void afterJob(@NonNull JobExecution jobExecution) {
                System.out.println("🔸 [Tasklet Job] 종료: " + jobExecution.getStatus());
            }
        };
    }

}
