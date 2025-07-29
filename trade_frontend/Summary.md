# Summary

| Unnamed: 0 | 레벨 | .md | 제목 | 설명 | RS | Unnamed: 6 | Unnamed: 7 | Unnamed: 8 | Unnamed: 9 | Unnamed: 10 | Unnamed: 11 | Unnamed: 12 | Unnamed: 13 | Unnamed: 14 | Unnamed: 15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | meta | project | 프로젝트명 | nan | prj | id | name | version | nan | nan | nan | nan | nan | nan | nan |
| 2.0 | meta | goals | 프로젝트 목적 | nan | gol | id | name | nan | nan | cate1 | cate2 | priority | status | nan | description |
| 3.0 | meta | features | 주요 기능 | nan | fet | id | name | nan | nan | cate1 | cate2 | nan | status | nan | description |
| 4.0 | meta | stack | 기술/환경 스택 | nan | stk | id | name | parent_id | nan | version | cate1 | cate2 | nan | nan | description |
| nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| 5.0 | back | file | 폴더/파일 | nan | fil | id | name | parent_id | nan | ext | nan | nan | nan | nan | description |
| 6.0 | back | file_x_mod | nan | nan | nan | file_id | seq | mod_id | nan | nan | nan | nan | nan | nan | nan |
| 7.0 | back | mod | 모듈 | nan | mod | id | name | parent_id | nan | type | component | public | return | nan | description |
| 8.0 | back | param | 파라미터 | nan | par | id | name | mod_id | nan | param | default | nan | nan | nan | nan |
| 9.0 | back | annot | 어노테이션 | nan | ann | id | name | mod_id | nan | param | default | nan | nan | nan | description |
| 10.0 | back | mod_x_mod | nan | nan | nan | to_id | seq | from_id | nan | type | subj | action | obj | nan | description |
| 11.0 | back | query | 쿼리 | nan | qry | id | name | mod_id | nan | nan | nan | nan | nan | nan | description |
| 12.0 | back | table | 테이블 | nan | tbl | id | name | parent_id | nan | type | pk | fk | not_null | nan | description |
| 13.0 | back | table_add | 테이블 추가정보 | nan | tbla | id | nan | nan | nan | index | partition | enum | auto_inc | unique | nan |
| 14.0 | back | table_x_table | nan | nan | txt | to_id | from_id | nan | nan | nan | nan | nan | nan | nan | nan |
| 15.0 | back | end_x_mod | nan | nan | exm | end_id | mod_id | nan | nan | nan | nan | nan | nan | nan | nan |
| 16.0 | back | end | 엔드포인트 | nan | end | id | type | name | nan | method | req_param | req_body | response | nan | description |
| nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| 17.0 | front | html | 화면 | nan | htm | id | name | parent_id | nan | view | nan | nan | nan | nan | description |
| 18.0 | front | html_x_html | nan | nan | hxh | to_id | from_id | nan | nan | view | nan | nan | nan | nan | description |
| 19.0 | front | html_x_jst | nan | nan | hxj | to_id | from_id | nan | nan | nan | nan | nan | nan | nan | nan |
| 20.0 | front | jst | 스크립트 | nan | jst | id | name | parent_id | nan | type | component | public | return | nan | nan |
| 21.0 | front | attr | 속성 | nan | att | id | name | mod_id | nan | param | default | nan | nan | nan | nan |
| 22.0 | front | jst_x_end | nan | nan | jxe | end_id | jst_id | nan | nan | nan | nan | nan | nan | nan | nan |
| nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan | nan |
| 24.0 | rule | mod_x_rule | nan | nan | mxr | mod_id | rules_id | nan | nan | nan | nan | nan | nan | nan | nan |
| 25.0 | rule | coding | 코딩 규칙 | nan | cdr | id | name | nan | nan | cate1 | cate2 | status | use_yn | nan | description |
| 26.0 | rule | business | 비즈니스 규칙 | nan | bnr | id | name | nan | nan | cate1 | cate2 | status | use_yn | nan | description |
| 27.0 | rule | except | 예외 처리 | nan | ext | id | name | nan | nan | cate1 | cate2 | status | use_yn | nan | description |
| 28.0 | rule | workflow | 작업 흐름 | nan | wfw | id | name | seq | nan | cate1 | cate2 | nan | use_yn | nan | description |
| 29.0 | rule | document | 문서화 | nan | doc | id | name | nan | nan | cate1 | cate2 | status | use_yn | nan | description |
