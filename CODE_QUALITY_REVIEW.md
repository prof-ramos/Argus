# Revisão de Qualidade de Código — ARGUS

---

## 1. Convenções de Nomenclatura

### 1.1 Problemas Encontrados

#### N1 — Typo no nome da classe `MaigreCollector`

**Arquivos:** `collectors/maigret.py:12`, `collectors/__init__.py:3`, `argus.py:8`

O módulo chama-se `maigret.py` (nome correto da ferramenta), mas a classe dentro dele está nomeada como `MaigreCollector` — faltando o "t". Isso é uma inconsistência que gera confusão:

```python
# collectors/maigret.py:12
class MaigreCollector:     # ← falta "t" — deveria ser MaigretCollector
    def __init__(self):
        self.name = "Maigret"   # aqui o nome está correto
        self.command = "maigret" # aqui também
```

O atributo `self.name` e `self.command` usam "Maigret" corretamente, mas o nome da classe não.

**Impacto:** Qualquer desenvolvedor novo terá dúvida se é intencional. Todos os imports propagam o typo (`from collectors.maigret import MaigreCollector`).

---

#### N2 — Parâmetro `username` usado genericamente para target

**Arquivos:** `ai/report_generator.py:25`, `ai/prompt_builder.py:6`, `output/formatter.py:10,20,91`

Múltiplos métodos recebem `username: str` como parâmetro, mas na prática o valor pode ser um email:

```python
# ai/report_generator.py:25
def generate(self, username: str, results: List[Dict], search_type: str = "username") -> Optional[AIReport]:

# output/formatter.py:10
def to_json(username: str, results: List[Dict], ...) -> str:

# argus.py:63-64 — chamada real
gen.generate(
    username or email,    # ← pode ser email
    enriched,
    "username" if username else "email"
)
```

O nome `username` engana — quando o usuário busca por `--email`, o valor passado é um email, não um username. Um nome como `target` seria preciso em todos os contextos.

---

#### N3 — Inconsistência de idioma em nomes e strings

**Vários arquivos**

O código mistura português e inglês de forma inconsistente:

```python
# argus.py:33 — mensagem em português
console.print("[red]Especifique --username ou --email[/red]")

# collectors/maigret.py:68 — erro em português
raise RuntimeError(error_msg or f"{self.command} falhou com exit code {proc.returncode}")

# collectors/maigret.py:72 — erro em português sem acento
raise RuntimeError(f"{self.command} nao gerou arquivo JSON de saida")

# processing/enricher.py:19 — log em inglês
logger.warning("Could not load platforms_metadata.json: %s. Using empty metadata.", e)

# processing/filter.py:48 — log em inglês
logger.debug("Validation failed for %s: %s: %s", ...)
```

**Padrão observado:**
- Mensagens para o **usuário** (CLI) → português
- Mensagens de **log/exceção** internas → mistura de PT e EN
- **Docstrings** dos testes → inglês
- **Nomes de variáveis/classes** → inglês

**Sugestão:** Definir convenção explícita: user-facing = PT-BR, logs/exceptions/code = EN.

---

#### N4 — `output_format` como string livre em vez de Enum

**Arquivo:** `argus.py:26,72-91`

```python
output_format: str = typer.Option("cli", "--format", "-f", help="Formato: cli, json, html")

# Depois verificado por comparação de string
if output_format == "json":
    ...
elif output_format == "html":
    ...
else:  # assume CLI para qualquer valor desconhecido
    ...
```

Qualquer string inválida (ex: `--format xml`) cai silenciosamente no `else` e produz output CLI sem aviso. Usar um `Enum` ou `typer.Option` com `case_sensitive=False` e valores fixos seria mais seguro.

---

### 1.2 Bons Padrões de Nomenclatura

#### BN1 — Enum `ResultStatus` com valores semânticos claros

```python
# collectors/base.py:6-10
class ResultStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    TIMEOUT = "timeout"
```

Nomes autoexplicativos, valores em snake_case consistentes. Excelente.

#### BN2 — Prefixo `_` para métodos privados nos collectors

```python
# collectors/maigret.py
async def _run_maigret(self, username: str) -> dict:     # privado
def _parse_results(self, maigret_output: dict) -> ...:   # privado
def _resolve_executable(self) -> str:                     # privado

# processing/filter.py
async def _validate_single(self, session, result) -> ...: # privado
def _is_404_redirect(url: str) -> bool:                   # module-level privado
```

Convenção Python respeitada consistentemente.

#### BN3 — `__all__` explícito em todos os `__init__.py`

```python
# collectors/__init__.py
__all__ = ["AccountResult", "ResultStatus", "MaigreCollector", "HoleheCollector"]

# processing/__init__.py
__all__ = ["Normalizer", "FalsePositiveFilter", "Enricher"]
```

Todos os 4 pacotes declaram `__all__`, tornando a API pública explícita.

---

## 2. Organização do Código

### 2.1 Problemas Encontrados

#### O1 — Import não utilizado

**Arquivo:** `argus.py:2`

```python
import webbrowser  # linha 2 — import no topo
```

E depois na linha 87:

```python
if open_browser:
    import webbrowser  # re-importado condicionalmente
    webbrowser.open(output_file.as_uri())
```

O `webbrowser` é importado duas vezes — uma no topo (desnecessária) e outra condicionalmente dentro do `if`. O import do topo deveria ser removido.

---

#### O2 — Lógica de output duplicada no `argus.py`

**Arquivo:** `argus.py:72-91`

O bloco de escrita de arquivo é duplicado entre `json` e `html`:

```python
# JSON — linhas 75-78
output_file = OUTPUT_DIR / f"{username or email}_report.json"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(output)
console.print(f"[green]Salvo: {output_file}[/green]")

# HTML — linhas 82-85 (mesmo padrão)
output_file = OUTPUT_DIR / f"{username or email}_report.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(output)
console.print(f"[green]Salvo: {output_file}[/green]")
```

4 linhas idênticas exceto pela extensão do arquivo. Poderia ser uma função auxiliar `_save_report(content, target, extension)`.

---

#### O3 — `Normalizer` como classe com método estático único

**Arquivo:** `processing/normalizer.py:5-21`

```python
class Normalizer:
    @staticmethod
    def normalize(all_results: List[List[AccountResult]]) -> List[AccountResult]:
        ...
```

A classe não tem estado, construtor, nem outros métodos. É uma função disfarçada de classe. Uma função simples `normalize()` no módulo seria mais Pythônica. O mesmo vale para `PromptBuilder`:

```python
# ai/prompt_builder.py:4-6
class PromptBuilder:
    @staticmethod
    def build(username: str, results: List[Dict], ...) -> str:
```

---

#### O4 — `ReportFormatter` instanciado mas usa apenas métodos estáticos

**Arquivo:** `argus.py:70` vs `output/formatter.py`

```python
# argus.py:70
formatter = ReportFormatter()  # instância criada

# output/formatter.py — todos os métodos são @staticmethod
@staticmethod
def to_json(...): ...
@staticmethod
def to_html(...): ...
@staticmethod
def to_cli(...): ...
```

A instância é desnecessária — `ReportFormatter.to_json(...)` funcionaria diretamente. A instanciação sugere falsamente que a classe tem estado.

---

#### O5 — `OUTPUT_DIR` importado no `formatter.py` mas não utilizado

**Arquivo:** `output/formatter.py:5`

```python
from config.settings import OUTPUT_DIR  # importado mas nunca usado no arquivo
```

A escrita de arquivo acontece no `argus.py`, não no formatter. Este import é morto.

---

### 2.2 Bons Padrões de Organização

#### BO1 — Separação clara em camadas por diretório

```
collectors/  → coleta de dados (I/O externo)
processing/  → transformação de dados (lógica pura)
ai/          → integração com LLM
output/      → formatação de saída
config/      → configuração
```

Cada diretório tem um propósito singular e bem definido. É fácil localizar onde qualquer funcionalidade reside.

#### BO2 — Testes organizados por feature com docstrings descritivas

```python
# tests/e2e/test_search_username.py
class TestSearchUsername:
    def test_search_username_exits_successfully(self, ...):
        """CLI exits with code 0 on a valid username search."""

class TestVersionCommand:
    def test_version_command_shows_version(self, ...):
        """'argus version' outputs the version string."""
```

Cada teste tem docstring explicando o comportamento esperado, e as classes agrupam testes por feature.

#### BO3 — Fixtures centralizadas no `conftest.py`

O `conftest.py` é bem organizado com seções claras separadas por comentários:

```python
# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# CLI runner fixture
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------
```

---

## 3. Tratamento de Erros

### 3.1 Problemas Encontrados

#### E1 — `except Exception` excessivamente amplo no `ReportGenerator`

**Arquivo:** `ai/report_generator.py:69-71`

```python
try:
    response = self.client.chat.completions.create(...)
    # ... 30 linhas de lógica ...
except Exception as e:
    logger.error("ReportGenerator error: %s: %s", type(e).__name__, e)
    return None
```

O `try` abrange 35 linhas e o `except Exception` captura **tudo** — erros de rede, `KeyError`, `TypeError`, `AttributeError` de bugs no código, etc. Um bug no parsing do `AIReport` (linhas 51-67) seria silenciosamente engolido e retornaria `None`.

**Sugestão:** Separar o `try/except` em blocos menores:
- Um para a chamada da API (`openai.APIError`, `openai.AuthenticationError`)
- Outro para o parsing JSON (já existe na linha 47)
- Deixar bugs internos propagarem

---

#### E2 — Mutação silenciosa de `AccountResult` no filter

**Arquivo:** `processing/filter.py:44`

```python
async def _validate_single(self, session, result):
    ...
    if resp.status == 200:
        result.http_status = 200  # ← muta o objeto de entrada
        return result
```

O filtro modifica o `AccountResult` original diretamente em vez de criar uma cópia. Isso é um side effect não óbvio — quem chama `filter()` não espera que os objetos de entrada sejam alterados. O `conftest.py` na fixture `mock_filter_passthrough` usa `copy.copy(result)` corretamente, reconhecendo implicitamente esse problema.

---

#### E3 — `formatter.to_html` crasheia se `url` for `None`

**Arquivo:** `output/formatter.py:27-29`

```python
platforms_html = "\n".join([
    f"""
    <div class="platform-card">
        <h3>{html_lib.escape(r['site_name'])}</h3>
        <a href="{html_lib.escape(r['url'])}" ...>   # ← crash se r['url'] é None
            {html_lib.escape(r['url'])}               # ← crash aqui também
        </a>
        <span class="category">{html_lib.escape(r['metadata']['category'])}</span>
    </div>
    """ for r in results
])
```

`html_lib.escape(None)` levanta `TypeError`. O `HoleheCollector` retorna resultados com `url=None` (ver `conftest.py:51`), então esse cenário é real. A versão CLI tem o mesmo problema:

```python
# formatter.py:104
table.add_row(r["site_name"], r["metadata"]["category"])
# ← sem KeyError guard; funciona por sorte porque Enricher sempre adiciona "category"
```

---

#### E4 — Ausência de validação no `output_format`

**Arquivo:** `argus.py:72-91`

```python
if output_format == "json":
    ...
elif output_format == "html":
    ...
else:
    formatter.to_cli(...)  # qualquer formato inválido cai aqui silenciosamente
```

`argus search --format invalid_value` produz output CLI sem nenhum aviso. O usuário pode não perceber que digitou errado.

---

#### E5 — `COLLECTOR_RETRIES` definido mas nunca utilizado

**Arquivo:** `config/settings.py:17`

```python
COLLECTOR_RETRIES = int(os.getenv("COLLECTOR_RETRIES", 2))
```

A variável é configurável mas nenhum collector implementa retry. Se a intenção era ter retries, a implementação está incompleta. Se não era, a variável é dead code que confunde.

---

### 3.2 Bons Padrões de Tratamento de Erros

#### BE1 — Collectors nunca propagam exceções

```python
# collectors/maigret.py:17-41
async def collect(self, username: str) -> List[AccountResult]:
    try:
        result = await asyncio.wait_for(...)
        return self._parse_results(result)
    except asyncio.TimeoutError:
        return [AccountResult(site_name="Maigret", status=ResultStatus.TIMEOUT, error="Timeout")]
    except (OSError, ValueError) as e:
        return [AccountResult(site_name="Maigret", status=ResultStatus.ERROR, error=str(e))]
    except Exception as e:
        return [AccountResult(site_name="Maigret", status=ResultStatus.ERROR, error=f"{type(e).__name__}: {e}")]
```

Este é um dos melhores padrões do projeto. Garante que:
- O pipeline **nunca** crasheia por causa de um collector
- Erros são **capturados como dados** (AccountResult com status de erro)
- A hierarquia de exceções é **específica primeiro** (TimeoutError → OSError/ValueError → Exception)

Ambos os collectors seguem o mesmo padrão consistentemente.

#### BE2 — Graceful degradation no Enricher

```python
# processing/enricher.py:13-21
try:
    with open(metadata_path, encoding="utf-8") as f:
        raw = json.load(f)
        self.platform_data = raw["platforms"]
        self.aliases = raw.get("aliases", {})
except (OSError, json.JSONDecodeError, KeyError) as e:
    logger.warning("Could not load platforms_metadata.json: %s. Using empty metadata.", e)
    self.platform_data = {}
    self.aliases = {}
```

Se o JSON de metadados estiver ausente ou corrompido, o Enricher continua funcionando com metadados vazios. O pipeline não para.

#### BE3 — Validação de input no HoleheCollector

```python
# collectors/holehe.py:19-24
if not _EMAIL_RE.match(email):
    return [AccountResult(
        site_name="Holehe",
        status=ResultStatus.ERROR,
        error=f"Invalid email format: {email!r}"
    )]
```

Valida o email **antes** de lançar o subprocess, evitando execução desnecessária. Usa o mesmo padrão de retornar erro como dado.

#### BE4 — Lazy init com validação no ReportGenerator

```python
# ai/report_generator.py:25-27
def generate(self, ...):
    if not self.api_key:
        raise ValueError("OPENAI_API_KEY not configured")
```

A API key é validada no momento do uso, não no import. Combinado com o lazy init da property `client`, garante que nenhuma conexão é feita sem necessidade.

---

## 4. Práticas de Comentários

### 4.1 Problemas Encontrados

#### C1 — Ausência total de docstrings nos módulos de produção

Nenhum dos módulos de produção tem docstrings nas classes ou métodos públicos:

```python
# processing/enricher.py
class Enricher:                    # sem docstring
    def enrich(self, results):     # sem docstring

# processing/normalizer.py
class Normalizer:                  # sem docstring
    def normalize(all_results):    # sem docstring

# collectors/maigret.py
class MaigreCollector:             # sem docstring
    async def collect(self, ...):  # sem docstring

# output/formatter.py
class ReportFormatter:             # sem docstring
    def to_json(self, ...):        # sem docstring
    def to_html(self, ...):        # sem docstring
    def to_cli(self, ...):         # sem docstring
```

A única docstring de método em todo o código de produção é:

```python
# ai/report_generator.py:19
@property
def client(self) -> "OpenAI":
    """Lazy-initialize OpenAI client only when first needed."""
```

E uma função auxiliar:

```python
# processing/filter.py:52-53
def _is_404_redirect(url: str) -> bool:
    """Return True if the final URL looks like a 404/not-found redirect."""
```

**Impacto:** Os type hints compensam parcialmente, mas os métodos `enrich`, `normalize`, `filter` e `collect` não documentam seus contratos (ex: "nunca levanta exceções", "flatten + deduplica").

---

#### C2 — Comentários inline no `argus.py` são genéricos demais

```python
# argus.py:40
# Coleta

# argus.py:52
# Processamento

# argus.py:58
# IA

# argus.py:69
# Output
```

Esses comentários são rótulos de seção que repetem o que o código já diz. Não adicionam valor. Se a orquestração estivesse em uma classe Pipeline, os nomes dos métodos (`collect`, `process`, `analyze`, `format`) seriam autoexplicativos.

---

#### C3 — Strings de erro sem acentos

```python
# collectors/maigret.py:72
raise RuntimeError(f"{self.command} nao gerou arquivo JSON de saida")

# collectors/maigret.py:113
raise FileNotFoundError(f"{self.command} nao instalado no ambiente do projeto")
```

Mensagens em português sem acentos ("nao" em vez de "não", "saida" em vez de "saída"). Se a decisão é usar PT-BR, os acentos devem estar presentes. Se é manter ASCII, deveria ser em inglês.

---

### 4.2 Bons Padrões de Comentários

#### BC1 — Docstrings excelentes em todos os testes

```python
# tests/e2e/test_search_username.py
def test_search_username_exits_successfully(self, ...):
    """CLI exits with code 0 on a valid username search."""

def test_search_username_normalizer_deduplicates(self, ...):
    """Normalizer removes duplicate results (same site_name + url)."""

def test_search_username_with_no_results(self, ...):
    """When no platforms are found, CLI exits cleanly without crash."""
```

Cada teste documenta **o comportamento esperado**, não a implementação. Seguem o padrão "Given/When/Then" implícito. Consistentemente em inglês.

#### BC2 — Docstrings nas fixtures explicam o propósito do mock

```python
# tests/conftest.py:136-141
@pytest.fixture
def mock_ai_generate(sample_ai_report):
    """Patch ReportGenerator in argus module to return a canned AIReport.

    Patches the class itself so that __init__ (which creates an OpenAI client)
    is never called, and generate() returns the sample report.
    """
```

Explica **por que** o mock é feito dessa forma (evitar `__init__` do OpenAI client), não apenas o que faz.

#### BC3 — Separadores de seção no `conftest.py`

```python
# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
```

Ajudam na navegação visual do arquivo. Usado consistentemente para 4 seções lógicas.

---

## Resumo Consolidado

| Área | Nota | Principais Problemas |
|------|------|---------------------|
| **Nomenclatura** | Média | Typo `MaigreCollector`, `username` genérico, idioma misto |
| **Organização** | Boa | Import morto, lógica duplicada no output, classes-funções |
| **Tratamento de Erros** | Boa | `except Exception` amplo na AI, mutação no filter, `None` no HTML |
| **Comentários** | Média | Zero docstrings em produção, testes excelentes |

### Top 5 Correções Prioritárias

1. **Renomear `MaigreCollector` → `MaigretCollector`** — typo que afeta toda a base
2. **Renomear parâmetro `username` → `target`** no formatter, prompt_builder e report_generator
3. **Adicionar guard para `url=None`** no `formatter.to_html` e `formatter.to_cli`
4. **Reduzir escopo do `except Exception`** no `report_generator.py` — separar API errors de bugs
5. **Remover import morto** `webbrowser` no topo do `argus.py` e `OUTPUT_DIR` no `formatter.py`
