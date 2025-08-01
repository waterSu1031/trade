# CORS 설정 가이드

## 1. Python FastAPI 백엔드 (포트 8000)

FastAPI에서 CORS를 설정하려면 다음 코드를 추가하세요:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 개발 서버
        "http://localhost:4173",  # Vite 프리뷰 서버
        "http://localhost:3000",  # 프로덕션 포트 (필요시)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 2. Spring Boot 백엔드 (포트 8080)

Spring Boot에서 CORS를 설정하는 방법:

### 방법 1: @CrossOrigin 어노테이션 (컨트롤러 레벨)

```java
@RestController
@RequestMapping("/api/batch")
@CrossOrigin(origins = {"http://localhost:5173", "http://localhost:4173"})
public class BatchController {
    // ...
}
```

### 방법 2: 전역 CORS 설정 (권장)

```java
@Configuration
public class CorsConfig {
    
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                    .allowedOrigins(
                        "http://localhost:5173",
                        "http://localhost:4173",
                        "http://localhost:3000"
                    )
                    .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                    .allowedHeaders("*")
                    .allowCredentials(true)
                    .maxAge(3600);
            }
        };
    }
}
```

### 방법 3: application.properties 설정

```properties
# CORS 설정
spring.web.cors.allowed-origins=http://localhost:5173,http://localhost:4173
spring.web.cors.allowed-methods=GET,POST,PUT,DELETE,OPTIONS
spring.web.cors.allowed-headers=*
spring.web.cors.allow-credentials=true
```

## 3. WebSocket CORS 설정 (Python)

WebSocket 연결을 위한 CORS 설정:

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocket은 기본적으로 CORS를 우회하지만,
    # 필요시 Origin 헤더를 확인할 수 있습니다
    origin = websocket.headers.get("origin")
    allowed_origins = ["http://localhost:5173", "http://localhost:4173"]
    
    if origin not in allowed_origins:
        await websocket.close(code=403, reason="Forbidden")
        return
    
    await websocket.accept()
    # ... WebSocket 로직
```

## 4. 프로덕션 환경 고려사항

프로덕션 환경에서는 보안을 위해 더 엄격한 CORS 설정을 사용하세요:

1. 와일드카드(*) 대신 구체적인 도메인 지정
2. 필요한 HTTP 메서드만 허용
3. 민감한 헤더는 제한적으로 허용
4. credentials는 필요한 경우에만 true로 설정

## 5. 문제 해결

CORS 에러가 발생하면:

1. 브라우저 개발자 도구의 Network 탭에서 실제 요청 확인
2. Preflight (OPTIONS) 요청이 성공하는지 확인
3. 응답 헤더에 Access-Control-Allow-Origin이 포함되었는지 확인
4. 서버 로그에서 CORS 관련 에러 확인