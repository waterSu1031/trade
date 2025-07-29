from textwrap import dedent
import pandas as pd
import ace_tools as tools

# 각 테이블에 대한 CRUD용 Repository 인터페이스 (JPA 기반)
# 필드 이름은 테이블 정의에 따라 맞추고, Entity 클래스는 CamelCase로 변환

entities = [
    "Exchange", "ExcXSym", "Symbol", "SymXData",
    "SymbolFromCsv", "SymbolInterval"  # SymbolInterval은 symbol_interval 테이블과 매핑됨
]


def generate_jpa_repositories(entities):
    result = []
    for entity in entities:
        repository = dedent(f"""
            package com.trade.jpa.repository;

            import com.trade.jpa.model.{entity};
            import org.springframework.data.jpa.repository.JpaRepository;
            import org.springframework.stereotype.Repository;

            @Repository
            public interface {entity}Repository extends JpaRepository<{entity}, Long> {{
                // 필요한 경우 커스텀 쿼리 메서드 추가
            }}
        """)
        result.append((entity, repository.strip()))
    return result


repository_files = generate_jpa_repositories(entities)

df = pd.DataFrame(repository_files, columns=["Entity", "RepositoryInterface"])
tools.display_dataframe_to_user(name="JPA Repository Interfaces", dataframe=df)


def main():
    generate_jpa_repositories(entities)


if __name__ == "__main__":
    main()