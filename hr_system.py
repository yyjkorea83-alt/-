import datetime
from dateutil.relativedelta import relativedelta
import math

class CourtHRSystem:
    def __init__(self):
        self.promotion_req_months = {9: 66, 8: 84, 7: 132}
        self.treatment_req_months = {9: 48, 8: 48, 7: 48, 6: 48, 5: 84, 4: 84} 
        self.min_prom_months = {9: 18, 8: 24, 7: 24, 6: 42}

    def _get_next_quarter_start(self, target_date):
        next_quarter_month = ((target_date.month - 1) // 3 + 1) * 3 + 1
        if next_quarter_month > 12:
            return datetime.date(target_date.year + 1, 1, 1)
        return datetime.date(target_date.year, next_quarter_month, 1)

    def _get_next_month_start(self, target_date):
        return (target_date.replace(day=1) + relativedelta(months=1))

    def calc_disciplinary_exclusion(self, disc_type, disc_duration, is_aggravated):
        exclusion = 0
        if disc_type == "강등" or disc_type == "정직":
            exclusion = disc_duration + 18
        elif disc_type == "감봉":
            exclusion = disc_duration + 12
        elif disc_type == "견책":
            exclusion = 6
        if disc_type != "없음" and is_aggravated:
            exclusion += 6
        return exclusion

    # [신규 모듈] 역(曆)에 따른 기간 자동 계산 및 15일 절상 룰 적용
    def calc_career_months(self, start_d, end_d, ex_y=0, ex_m=0, ex_d=0):
        if not start_d or not end_d or start_d > end_d:
            return 0
        
        # 종료일 당일까지 포함하기 위해 1일을 더함
        temp_end = end_d + relativedelta(days=1)
        rd = relativedelta(temp_end, start_d)
        
        # 제외기간(휴직 등) 차감
        total_y = rd.years - ex_y
        total_m = rd.months - ex_m
        total_d = rd.days - ex_d
        
        # 음수 일/월 보정 (1월 = 30일 기준)
        while total_d < 0:
            total_m -= 1
            total_d += 30 
        while total_m < 0:
            total_y -= 1
            total_m += 12
            
        while total_d >= 30:
            total_m += 1
            total_d -= 30
        while total_m >= 12:
            total_y += 1
            total_m -= 12
            
        # [법원 규정] 잔여 일수가 15일 이상인 경우 1개월로 산입
        if total_d >= 15:
            total_m += 1
            
        if total_m >= 12:
            total_y += 1
            total_m -= 12
            
        return max(0, total_y * 12 + total_m)

    def calc_promotion_date(self, current_rank_date, rank, reg_career, spec_career, exclusion_months):
        req_months = self.promotion_req_months.get(rank, 0)
        recognized_spec = min(spec_career * 0.5, req_months * 0.5)
        total_recognized_career = reg_career + recognized_spec
        total_months_to_add = req_months - total_recognized_career + exclusion_months
        qualify_date = current_rank_date + relativedelta(months=int(total_months_to_add))
        qualify_date_next_day = qualify_date + relativedelta(days=1)
        return self._get_next_quarter_start(qualify_date_next_day), total_recognized_career

    def calc_treatment_officer_date(self, current_rank_date, rank, reg_career, spec_career, exclusion_months):
        req_months = self.treatment_req_months.get(rank, 48)
        min_prom = self.min_prom_months.get(rank, 18)
        converted_spec = spec_career * 0.5
        step_1_spec = min(converted_spec, min_prom * 0.5)
        step_2_spec = (converted_spec - step_1_spec) * (2/3)
        total_credit = reg_career + step_1_spec + step_2_spec
        total_months_to_add = req_months - total_credit + exclusion_months
        qualify_date = current_rank_date + relativedelta(months=math.ceil(total_months_to_add))
        return self._get_next_month_start(qualify_date), total_credit

    def calc_step_up_date(self, current_step_date, leave_months, is_second_child_or_both_parents=False):
        unpaid_leave = max(leave_months - 12, 0)
        exclusion_months = 0 if is_second_child_or_both_parents else unpaid_leave 
        return current_step_date + relativedelta(years=1, months=exclusion_months)

    def calc_career_score(self, gap_m, eul_m, byung_m, jung_m, rank):
        P_GAP_BASIC = 0.47
        P_EUL_BASIC = 0.38
        P_EUL_EXCESS = 0.10
        P_GAP_EXCESS = 0.1175 
        P_BYUNG = 0.058 if rank <= 5 else 0.07
        P_JUNG = 0.050 if rank <= 5 else 0.06
        
        basic_gap = min(gap_m, 72)
        excess_gap = gap_m - basic_gap
        remaining_cap = 72 - basic_gap
        basic_eul = min(eul_m, remaining_cap)
        excess_eul = eul_m - basic_eul
        
        score_gap_basic = basic_gap * P_GAP_BASIC
        score_gap_excess = excess_gap * P_GAP_EXCESS
        score_eul_basic = basic_eul * P_EUL_BASIC
        score_eul_excess = excess_eul * P_EUL_EXCESS
        score_byung = min(byung_m * P_BYUNG, 8.40)
        score_jung = min(jung_m * P_JUNG, 7.20)
        
        total_score = score_gap_basic + score_gap_excess + score_eul_basic + score_eul_excess + score_byung + score_jung
        total_score = min(total_score, 40.00) 
        
        return {
            "기본_갑_월": basic_gap, "기본_을_월": basic_eul, "초과_갑_월": excess_gap, "초과_을_월": excess_eul,
            "기본_갑_점": round(score_gap_basic, 2), "기본_을_점": round(score_eul_basic, 2),
            "초과_갑_점": round(score_gap_excess, 2), "초과_을_점": round(score_eul_excess, 2),
            "병_점": round(score_byung, 2), "정_점": round(score_jung, 2), "최종점수": round(total_score, 2)
        }