# 미환류소득 시나리오 프로그램

예상 기업소득과 투자·배당·임금증가·상생협력 계획을 입력하면 투자포함형과 투자제외형의 **당기 예상 미환류소득**을 비교할 수 있는 Streamlit 기반 Tax Planning 보조도구입니다.

> 모든 금액 단위: **백만원**  
> 법령 기준일: **2026-07-20**  
> Version: **0.2.1**

## 주요 기능

- 투자포함형(80%)과 투자제외형(30%) 동시 계산
- 투자액: 당기 실제 지출액에서 제외항목을 차감해 잠정 적격 투자액 계산
- 배당액: 결의·계상 총액에서 주식배당, 준비금 감액배당, 미지급배당금 등을 차감
- 임금증가액: 상시근로자 증가 여부에 따라 입력 화면과 계산식 분기
- 상생협력 지출액: 실제 적격 지출액의 300%를 환류 인정액으로 반영
- 기한이 도래한 과거 차기환류적립금과 당기 초과환류액 정산
- 이월 초과환류액과 당기 신규 차기환류적립금 반영
- 기준 시나리오와 사용자가 직접 추가한 기업소득 시나리오 비교
- 투자포함형·투자제외형의 당기 인정 환류액 표시
- 입력값 오류 및 제외금액 초과 경고

## 화면 구성

1. **입력 및 상세 산정**  
   기업소득·이월항목과 투자·배당·임금·상생협력 관련 금액을 입력합니다.

2. **기준 결과**  
   투자포함형과 투자제외형의 당기 예상 미환류소득을 비교하고, 상세 계산내역을 확인합니다.

3. **시나리오 비교**  
   기준 시나리오 외에 기업소득 시나리오를 직접 추가해 결과를 카드 형태로 비교합니다.

4. **계산 근거·한계**  
   핵심 산식과 프로그램의 적용 범위를 확인합니다.

## 프로젝트 구조

현재 GitHub 저장소 기준 파일 구성은 다음과 같습니다.

```text
Unrepatriated-Income-Tax-Simulator/
├── streamlit_app.py       # Streamlit 화면 및 사용자 입력
├── tax_model.py           # 미환류소득 계산 로직
├── requirements.txt       # 실행에 필요한 패키지
├── README.md              # 프로젝트 설명서
├── VALIDATION.md          # 검증 내역
├── .gitignore             # GitHub 제외 파일 설정
├── example_scenarios.csv  # 예시 시나리오 데이터
└── test_tax_model.py      # 계산 로직 테스트
```

# 로컬 실행 방법

아래 설명은 **Windows와 VS Code 기준**입니다.

## 1. 준비사항

다음 프로그램이 설치되어 있어야 합니다.

- Python 3.11 이상 권장
- Visual Studio Code

설치 여부는 VS Code 터미널에서 다음 명령으로 확인할 수 있습니다.

```powershell
py --version
```

`Python 3.x.x`가 표시되면 정상입니다.

## 2. 프로젝트 내려받기

GitHub 저장소 상단에서 다음을 선택합니다.

```text
Code → Download ZIP
```

ZIP 파일의 압축을 푼 뒤 VS Code에서 해당 폴더를 엽니다.

```text
File → Open Folder
```

또는 Git이 설치되어 있다면 다음 명령으로 저장소를 복제할 수 있습니다.

```powershell
git clone https://github.com/leewjcpa-rgb/Unrepatriated-Income-Tax-Simulator.git
cd Unrepatriated-Income-Tax-Simulator
```

## 3. VS Code 터미널 열기

VS Code 상단 메뉴에서 다음을 선택합니다.

```text
Terminal → New Terminal
```

터미널의 현재 위치가 프로젝트 폴더인지 확인합니다. 다음 파일들이 보여야 합니다.

```text
streamlit_app.py
tax_model.py
requirements.txt
```

## 4. 필요한 패키지 설치

터미널에 다음 명령을 입력합니다.

```powershell
py -m pip install -r requirements.txt
```

이미 설치된 패키지는 `Requirement already satisfied`로 표시될 수 있으며 정상입니다.

## 5. 앱 실행

다음 명령을 입력합니다.

```powershell
py -m streamlit run streamlit_app.py
```

Streamlit을 처음 실행하면 이메일 입력을 요청할 수 있습니다.
이메일 수신을 원하지 않으면 아무것도 입력하지 않고 **Enter**를 누릅니다.

브라우저가 자동으로 열리지 않으면 아래 주소로 접속합니다.

```text
http://localhost:8501
```

## 6. 앱 종료

VS Code 터미널에서 다음 키를 누릅니다.

```text
Ctrl + C
```


## macOS / Linux 실행

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run streamlit_app.py
```

브라우저가 자동으로 열리지 않으면 다음 주소로 접속합니다.

```text
http://localhost:8501
```

# 테스트 실행

테스트에는 `pytest`가 필요합니다. 먼저 설치합니다.

```powershell
py -m pip install pytest
```

그다음 프로젝트 폴더에서 실행합니다.

```powershell
py -m pytest -q
```

정상이라면 다음과 같이 표시됩니다.

```text
5 passed
```

# Streamlit Community Cloud 배포

1. 프로젝트 파일을 GitHub 저장소에 업로드합니다.
2. Streamlit Community Cloud에 로그인합니다.
3. 해당 GitHub 저장소를 선택합니다.
4. Main file path를 `streamlit_app.py`로 지정합니다.
5. Deploy를 누릅니다.

`requirements.txt`가 저장소에 포함되어 있어 배포 환경에서 필요한 패키지가 자동으로 설치됩니다.

배포가 완료되면 아래에 실제 웹앱 주소를 추가할 수 있습니다.

[웹앱 바로 실행하기](https://unrepatriated-income-tax-simulator-crmca5al7cr9qvffefjsd2.streamlit.app/)

# 핵심 산식

```text
[투자포함형 A]
당기 산식 결과
= 기업소득 × 80%
- 투자액
- 배당액
- 임금증가 인정액
- 상생협력 지출액 × 300%

[투자제외형 B]
당기 산식 결과
= 기업소득 × 30%
- 배당액
- 임금증가 인정액
- 상생협력 지출액 × 300%
```

- 산식 결과가 양수이면 당기 미환류소득입니다.
- 산식 결과가 음수이면 그 절댓값을 초과환류액으로 봅니다.
- 당기 미환류소득에서는 이월 초과환류액과 당기 새로 설정한 차기환류적립금을 반영합니다.
- 과거 차기환류적립금 중 당기 정산기한이 도래한 금액은 당기 초과환류액으로 정산하고, 부족분에 20%를 적용합니다.

# 계산 모듈의 범위와 한계

이 앱은 신고 프로그램이 아니라 **Tax Planning 보조도구**입니다.

- 적용대상 법인 여부와 기업소득 산정은 자동 판정하지 않습니다.
- 투자·배당 모듈은 연간 합계에서 사용자가 입력한 제외항목을 차감하는 잠정 계산입니다.
- 임금 모듈은 사용자가 세법상 적격 상시근로자와 추가 인정금액을 검토했다는 전제입니다.
- 이월 초과환류액의 발생연도별 소멸기한은 별도로 관리해야 합니다.
- 투자자산 처분에 따른 추징 및 이자상당액은 포함하지 않습니다.
- 실제 세무신고나 세무의견을 대체하지 않습니다.

# 법령 참고

- 국가법령정보센터, 「조세특례제한법」 제100조의32  
  https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=900180783
- 국가법령정보센터, 「조세특례제한법 시행령」 제100조의32  
  https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000123033
- Streamlit 공식 문서  
  https://docs.streamlit.io/

# 프로젝트 설명 한 문장

> 미환류소득 산식만 계산하는 데 그치지 않고, 투자·배당·임금·상생협력 자료를 세법상 잠정 인정금액으로 변환한 뒤 사용자가 직접 설정한 기업소득 시나리오별 당기 예상 미환류소득을 비교하도록 만든 Tax Planning 보조도구입니다.
