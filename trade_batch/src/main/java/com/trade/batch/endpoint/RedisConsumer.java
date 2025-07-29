package com.trade.batch.endpoint;


// List/Stream 방식       =====================================================================

//import org.springframework.data.redis.core.StringRedisTemplate;
//import org.springframework.stereotype.Component;
//
//@Component
//public class RedisProducer {
//    private final StringRedisTemplate redisTemplate;
//
//    public RedisProducer(StringRedisTemplate redisTemplate) {
//        this.redisTemplate = redisTemplate;
//    }
//
//    public void send(String key, String message) {
//        redisTemplate.opsForList().rightPush(key, message);  // 리스트로 저장(큐)
//        // 또는 Streams 사용: XADD
//        // redisTemplate.opsForStream().add(MapRecord.create(key, map));
//    }
//}

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class RedisConsumer {
    private final StringRedisTemplate redisTemplate;

    public RedisConsumer(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public String receive(String key) {
        return redisTemplate.opsForList().leftPop(key);  // 큐에서 메시지 꺼내기
    }
}

// Pub/Sub 방식              =====================================================================
//import org.springframework.context.annotation.Bean;
//import org.springframework.context.annotation.Configuration;
//import org.springframework.data.redis.listener.PatternTopic;
//import org.springframework.data.redis.listener.RedisMessageListenerContainer;
//import org.springframework.data.redis.connection.RedisConnectionFactory;
//
//@Configuration
//public class RedisConfig {
//    @Bean
//    public RedisMessageListenerContainer container(RedisConnectionFactory connectionFactory, MyRedisListener listener) {
//        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
//        container.setConnectionFactory(connectionFactory);
//        container.addMessageListener(listener, new PatternTopic("trade"));  // "trade" 채널 구독
//        return container;
//    }
//}
//
//import org.springframework.data.redis.core.StringRedisTemplate;
//import org.springframework.stereotype.Component;
//
//@Component
//public class RedisPublisher {
//    private final StringRedisTemplate redisTemplate;
//
//    public RedisPublisher(StringRedisTemplate redisTemplate) {
//        this.redisTemplate = redisTemplate;
//    }
//
//    public void publish(String channel, String message) {
//        redisTemplate.convertAndSend(channel, message);
//    }
//}
//
//import org.springframework.data.redis.connection.Message;
//import org.springframework.data.redis.connection.MessageListener;
//import org.springframework.stereotype.Component;
//
//@Component
//public class MyRedisListener implements MessageListener {
//    @Override
//    public void onMessage(Message message, byte[] pattern) {
//        System.out.println("수신: " + message.toString());
//    }
//}