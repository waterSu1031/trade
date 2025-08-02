package com.trade.batch.endpoint;

import lombok.Getter;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.view.RedirectView;

import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

// 1. 텍스트, JSON, 파일 등 API 반환용
@RestController
@RequestMapping
public class RestSampleController {

    // 1. 단순 텍스트
    @GetMapping("/text")
    public String text() {
        return "plain text";
    }

    // 2. JSON DTO 반환
    @GetMapping("/json")
    public UserDto json() {
        return new UserDto("kim", 30);
    }

    // 3. JSON List 반환
    @GetMapping("/list")
    public List<String> list() {
        return List.of("A", "B", "C");
    }

    // 4. JSON Map 반환
    @GetMapping("/map")
    public Map<String, Object> map() {
        return Map.of("key1", 123, "key2", "abc");
    }

    // 5. 파일 다운로드 (경로에 test.txt 파일 필요!)
    @GetMapping("/file")
    public ResponseEntity<Resource> file() throws MalformedURLException {
        Path path = Paths.get("test.txt"); // 프로젝트 루트에 test.txt 파일 필요
        Resource resource = new UrlResource(path.toUri());
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=test.txt")
                .body(resource);
    }

    // 6. HTTP 상태코드, 헤더 등 커스텀 응답
    @GetMapping("/status")
    public ResponseEntity<String> status() {
        return ResponseEntity
                .status(202)
                .header("X-Custom-Header", "myValue")
                .body("custom status and header");
    }

    // 7. Content-Type 별도 지정 (텍스트)
    @GetMapping(value = "/text2", produces = "text/plain")
    public String text2() {
        return "plain text2";
    }

    // 8. Content-Type 별도 지정 (json)
    @GetMapping(value = "/json2", produces = "application/json")
    public Map<String, String> json2() {
        return Map.of("key", "val");
    }

    // 9. 에러 코드 응답
    @GetMapping("/error")
    public ResponseEntity<String> error() {
        return ResponseEntity.status(200).body("Bad Request Example");
    }

    // 10. 리다이렉트
    @GetMapping("/redirect")
    public RedirectView redirect() {
        return new RedirectView("/text");
    }
}

// 2. HTML 뷰 반환은 별도 @Controller 필요 (템플릿 엔진 필요!)
@Controller
class SampleHtmlController {
    @GetMapping("/html")
    public String html(Model model) {
        model.addAttribute("message", "hello");
        return "sampleView"; // templates/sampleView.html 필요 (Thymeleaf 기준)
    }

    // 포워드
    @GetMapping("/forward")
    public String forward() {
        return "forward:/text";
    }
}

// 3. DTO 예시
@Getter
class UserDto {
    private String name;
    private int age;
    public UserDto(String name, int age) {
        this.name = name; this.age = age;
    }
}
