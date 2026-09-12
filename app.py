import streamlit as st
import datetime
from hr_system import CourtHRSystem

# ==========================================
# 🔒 [보안 통제] 실무자 전용 비밀번호 잠금 화면
# ==========================================
# 세션(Session)을 이용해 한 번 로그인하면 창을 닫기 전까지 유지합니다.
if "authorized" not in st.session_state:
    st.session_state.authorized = False

if not st.session_state.authorized:
    st.title("🔒 법원 인사검증 시스템 (인가자 전용)")
    st.info("이 프로그램은 특정 실무자만 접근할 수 있는 보안 시스템입니다.")
    
    pwd = st.text_input("접근 암호를 입력하세요", type="password")
    if st.button("접속 (Login)"):
        # 실무자들끼리 공유할 비밀번호를 아래에 설정하세요.
        if pwd == "청주지법인사26":  
            st.session_state.authorized = True
            st.rerun() # 정답이면 화면을 새로고침하여 본 프로그램을 띄움
        else:
            st.error("⚠️ 인가되지 않은 접근입니다. 비밀번호를 확인하세요.")
    
    # 비밀번호를 맞추기 전까지는 아래쪽 코드가 절대 실행되지 않도록 차단합니다.
    st.stop() 
# ==========================================

# (이 아래부터는 기존에 작성하신 hr = CourtHRSystem() 코드와 탭(Tab) 화면 코드를 그대로 두시면 됩니다!)
hr = CourtHRSystem()
st.set_page_config(page_title="사법부 인사검증 시스템 4.0", page_icon="⚖️", layout="wide")
# ... (이하 생략) ...
import streamlit as st
import datetime
from hr_system import CourtHRSystem

hr = CourtHRSystem()

st.set_page_config(page_title="사법부 인사검증 시스템 4.0", page_icon="⚖️", layout="wide")
st.title("⚖️ 법원 맞춤형 인사검증 시스템 4.0")
st.markdown("임용일과 기준일을 바탕으로 역(曆)에 따른 개월 수 자동 산출 및 제외기간(휴직)을 공제합니다.")

# ==========================================
# [공통 정보] 전역(Global) 설정으로 탭 전체에 영향
# ==========================================
st.subheader("👤 대상자 공통 정보")
col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    이름 = st.text_input("직원 이름", "김법원 실무관")
with col_g2:
    현재직급 = st.selectbox("현재 평가 직급", [9, 8, 7, 6, 5], format_func=lambda x: f"{x}급")
with col_g3:
    현직급임용일 = st.date_input("현직급 임용일 (YYYY-MM-DD)", datetime.date(2020, 1, 1))
st.divider()

tab1, tab2, tab3 = st.tabs(["[1] 근속/대우공무원 발령", "[2] 정기승급(호봉) 검증", "[3] 경력평정 점수 시뮬레이터"])

with tab1:
    st.header("📥 발령 요건 특수경력 및 징계 입력")
    col_career, col_penalty = st.columns(2)
    with col_career:
        일반직_원본 = st.number_input("일반 행정직 등 (100% 반영 개월수)", min_value=0, value=0)
        특정직_원본 = st.number_input("군인 등 특정직 (50% 원본 개월수)", min_value=0, value=0)
        기타_휴직 = st.number_input("기타 승진 제외기간(개월)", min_value=0, value=0)

    with col_penalty:
        징계종류 = st.selectbox("징계 처분", ["없음", "견책", "감봉", "정직", "강등"])
        징계기간 = st.number_input(f"{징계종류} 처분 기간 (개월)", min_value=1, value=1) if 징계종류 in ["감봉", "정직", "강등"] else 0
        가중여부 = st.checkbox("🚨 6개월 가산 비위 (음주운전, 성범죄 등)") if 징계종류 != "없음" else False
        징계_제외기간 = hr.calc_disciplinary_exclusion(징계종류, 징계기간, 가중여부)
        
    if st.button("🔍 발령일 검증 실행", type="primary", key="btn1"):
        총_제외기간 = 기타_휴직 + 징계_제외기간
        승진발령일, 승진_인정경력 = hr.calc_promotion_date(현직급임용일, 현재직급, 일반직_원본, 특정직_원본, 총_제외기간)
        대우발령일, 대우_인정경력 = hr.calc_treatment_officer_date(현직급임용일, 현재직급, 일반직_원본, 특정직_원본, 총_제외기간)
        
        st.success(f"✅ {현재직급}급 근속승진 발령 예정일: {승진발령일.strftime('%Y-%m-%d')}")
        st.info(f"✅ {현재직급}급 대우공무원 발령 예정일: {대우발령일.strftime('%Y-%m-%d')}")

with tab2:
    st.header("📥 호봉 승급 예외사항 통제")
    기존승급일 = st.date_input("현재 호봉 승급일", datetime.date(2023, 7, 1))
    휴직기간 = st.number_input("육아휴직 사용기간 (개월)", min_value=0, value=18)
    특례적용 = st.checkbox("둘째 자녀 이상이거나, 부모 모두 6개월 이상 사용")

    if st.button("🔍 정기승급일 검증 실행", type="primary", key="btn2"):
        다음승급일 = hr.calc_step_up_date(기존승급일, 휴직기간, 특례적용)
        st.success(f"✅ 다음 정기 승급일: {다음승급일.strftime('%Y-%m-%d')}")

# ==========================================
# 탭 3: 경력평정 (날짜 역산 및 제외기간/100%경력 통합 반영)
# ==========================================
with tab3:
    st.header("📅 경력 대상 기간 및 제외기간 설정")
    
    # 1단: 날짜 입력
    c3_1, c3_2 = st.columns(2)
    with c3_1:
        st.info("🔹 갑경력 산정: 현직급 임용일 ~ 평정기준일")
        평정기준일 = st.date_input("평정기준일 (보통 6.30 또는 12.31)", datetime.date(2026, 6, 30))
    with c3_2:
        st.info("🔹 을경력 산정: 직전직급 임용일 ~ 현직급 임용일 전날")
        직전직급임용일 = st.date_input("직전직급 임용일", datetime.date(2015, 1, 1))

    # 2단: 제외기간 (휴직 등) 입력
    st.markdown("##### ➖ 평정 제외기간 (휴직/징계 등 공제)")
    c_ex1, c_ex2 = st.columns(2)
    with c_ex1:
        갑_제외_년 = st.number_input("갑경력 제외 (년)", min_value=0, value=0)
        갑_제외_월 = st.number_input("갑경력 제외 (월)", min_value=0, value=0)
        갑_제외_일 = st.number_input("갑경력 제외 (일)", min_value=0, value=0)
    with c_ex2:
        을_제외_년 = st.number_input("을경력 제외 (년)", min_value=0, value=0)
        을_제외_월 = st.number_input("을경력 제외 (월)", min_value=0, value=0)
        을_제외_일 = st.number_input("을경력 제외 (일)", min_value=0, value=0)

    # 3단: 100% 추가 경력 및 특정직 입력
    st.markdown("##### ➕ 타 기관 전입 등 추가 합산 경력")
    c_add1, c_add2 = st.columns(2)
    with c_add1:
        일반직_갑_추가 = st.number_input("일반행정 100% 산입 (갑경력용 / 개월)", min_value=0, value=0)
        일반직_을_추가 = st.number_input("일반행정 100% 산입 (을경력용 / 개월)", min_value=0, value=0)
    with c_add2:
        병경력 = st.number_input("특정직 등 동일계급 이상 (병경력 월수)", min_value=0, value=0)
        정경력 = st.number_input("특정직 등 바로 하위계급 (정경력 월수)", min_value=0, value=0)
        
    st.divider()
    
    if st.button("🔍 최종 경력평정 자동 산출", type="primary", key="btn3"):
        # 1. 자동 역산 엔진 가동 (을경력은 현직급임용일 하루 전까지)
        을경력_종료일 = 현직급임용일 - datetime.timedelta(days=1)
        
        순수_갑_월수 = hr.calc_career_months(현직급임용일, 평정기준일, 갑_제외_년, 갑_제외_월, 갑_제외_일)
        순수_을_월수 = hr.calc_career_months(직전직급임용일, 을경력_종료일, 을_제외_년, 을_제외_월, 을_제외_일)
        
        # 2. 100% 경력 더하기
        최종_갑경력 = 순수_갑_월수 + 일반직_갑_추가
        최종_을경력 = 순수_을_월수 + 일반직_을_추가
        
        # 3. 점수 산출
        배정 = hr.calc_career_score(최종_갑경력, 최종_을경력, 병경력, 정경력, 현재직급)
        
        st.header(f"🏆 최종 경력평정 점수: {배정['최종점수']} 점")
        if 배정['최종점수'] >= 40.0:
            st.warning("⚠️ 법정 최고 한도인 40.00점에 도달했습니다.")
            
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            st.success(f"📊 기본경력 - 합계: {round(배정['기본_갑_점']+배정['기본_을_점'], 2)}점")
            st.metric(f"갑경력 ({배정['기본_갑_월']}개월)", f"{배정['기본_갑_점']}점", delta=f"역산 {순수_갑_월수} + 합산 {일반직_갑_추가}", delta_color="off")
            st.metric(f"을경력 ({배정['기본_을_월']}개월)", f"{배정['기본_을_점']}점", delta=f"역산 {순수_을_월수} + 합산 {일반직_을_추가}", delta_color="off")
            
            st.info(f"🎖️ 특정직 경력 - 합계: {round(배정['병_점']+배정['정_점'], 2)}점")
            st.metric(f"병경력", f"{배정['병_점']}점")
            st.metric(f"정경력", f"{배정['정_점']}점")
            
        with r_col2:
            st.error(f"🗑️ 초과경력 (점수 삭감) - 합계: {round(배정['초과_갑_점']+배정['초과_을_점'], 2)}점")
            st.metric(f"갑경력 초과 ({배정['초과_갑_월']}개월)", f"{배정['초과_갑_점']}점")
            st.metric(f"을경력 초과 ({배정['초과_을_월']}개월)", f"{배정['초과_을_점']}점")