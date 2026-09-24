import json
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from .models import Employee, Department, BudgetExpense

class CustomLoginView(LoginView):
    template_name = 'hr_budget/login.html'
    redirect_authenticated_user = True

@login_required
def dashboard_view(request):
    employees = Employee.objects.filter(status='Active')
    total_employees = employees.count()
    
    # Aggregates
    agg = employees.aggregate(total_salary=Sum('salary'), avg_salary=Avg('salary'))
    total_salary = agg['total_salary'] or Decimal('0.00')
    avg_salary = agg['avg_salary'] or Decimal('0.00')
    
    # Total monthly cost (salary + benefits + 35% charges)
    total_benefits = employees.aggregate(sum_ben=Sum('benefits_cost'))['sum_ben'] or Decimal('0.00')
    charges = total_salary * Decimal('0.35')
    total_cost_monthly = total_salary + total_benefits + charges
    
    # Annual budget projection (12 months + operating expenses)
    annual_payroll = total_cost_monthly * Decimal('12')
    total_ops_expenses = BudgetExpense.objects.aggregate(sum_exp=Sum('amount'))['sum_exp'] or Decimal('0.00')
    annual_budget = annual_payroll + total_ops_expenses

    context = {
        'total_employees': total_employees,
        'total_salary': total_salary,
        'avg_salary': avg_salary,
        'total_cost_monthly': total_cost_monthly,
        'annual_budget': annual_budget,
    }
    return render(request, 'hr_budget/dashboard.html', context)

@login_required
def employees_view(request):
    query = request.GET.get('q', '')
    dept_id = request.GET.get('dept', '')
    
    employees_list = Employee.objects.all().select_related('department', 'position').order_by('name')
    
    if query:
        employees_list = employees_list.filter(Q(name__icontains=query) | Q(cpf__icontains=query))
    if dept_id:
        employees_list = employees_list.filter(department_id=dept_id)
        
    paginator = Paginator(employees_list, 15)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)
    
    departments = Department.objects.all()
    
    context = {
        'employees': employees,
        'departments': departments,
        'query': query,
        'dept_id': dept_id,
    }
    return render(request, 'hr_budget/employees.html', context)

@login_required
def budget_view(request):
    active_employees = Employee.objects.filter(status='Active')
    
    total_monthly_salary = active_employees.aggregate(s=Sum('salary'))['s'] or Decimal('0.00')
    annual_payroll = total_monthly_salary * Decimal('12')
    
    total_monthly_benefits = active_employees.aggregate(b=Sum('benefits_cost'))['b'] or Decimal('0.00')
    annual_charges = (total_monthly_salary * Decimal('0.35') + total_monthly_benefits) * Decimal('12')
    
    expenses = BudgetExpense.objects.all().select_related('department').order_by('-year', '-month')
    total_expenses = expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    
    # Department costs
    departments = Department.objects.all()
    department_costs = []
    for d in departments:
        dept_emps = active_employees.filter(department=d)
        count = dept_emps.count()
        sal = dept_emps.aggregate(s=Sum('salary'))['s'] or Decimal('0.00')
        ben = dept_emps.aggregate(b=Sum('benefits_cost'))['b'] or Decimal('0.00')
        chg = sal * Decimal('0.35')
        total_cost = sal + ben + chg
        department_costs.append({
            'name': d.name,
            'count': count,
            'total_cost': total_cost
        })

    employees_list = [
        {
            'name': e.name,
            'dept': e.department.name,
            'cargo': e.position.title,
            'level': e.position.level,
            'sal': float(e.salary),
        }
        for e in active_employees
    ]

    context = {
        'annual_payroll': annual_payroll,
        'annual_charges': annual_charges,
        'total_expenses': total_expenses,
        'department_costs': department_costs,
        'expenses': expenses[:20],
        'employees_json': json.dumps(employees_list),
    }
    return render(request, 'hr_budget/budget.html', context)

@login_required
def simulator_view(request):
    active_employees = Employee.objects.filter(status='Active')
    base_headcount = active_employees.count()
    base_monthly_salary = active_employees.aggregate(s=Sum('salary'))['s'] or Decimal('0.00')
    base_monthly_benefits = active_employees.aggregate(b=Sum('benefits_cost'))['b'] or Decimal('0.00')
    base_charges = base_monthly_salary * Decimal('0.35')
    base_monthly_total = base_monthly_salary + base_monthly_benefits + base_charges
    base_annual_cost = base_monthly_total * Decimal('12')

    simulated_headcount = base_headcount
    simulated_monthly_payroll = base_monthly_salary
    simulated_monthly_total = base_monthly_total
    simulated_annual_cost = base_annual_cost
    cost_diff = Decimal('0.00')
    
    salary_increase = 0.0
    new_hires = 0
    terminations = 0

    if request.method == 'POST':
        try:
            salary_increase = float(request.POST.get('salary_increase', 0))
        except ValueError:
            salary_increase = 0.0
            
        try:
            new_hires = int(request.POST.get('new_hires', 0))
        except ValueError:
            new_hires = 0
            
        try:
            terminations = int(request.POST.get('terminations', 0))
        except ValueError:
            terminations = 0

        # Calculate simulation
        inc_factor = Decimal(str(1.0 + (salary_increase / 100.0)))
        simulated_salary = base_monthly_salary * inc_factor
        
        simulated_headcount = max(0, base_headcount + new_hires - terminations)
        
        # Average salary for adjustments
        avg_sal = (base_monthly_salary / base_headcount) if base_headcount > 0 else Decimal('5000.00')
        avg_ben = (base_monthly_benefits / base_headcount) if base_headcount > 0 else Decimal('1200.00')
        
        # Adjust for new hires and terminations
        net_headcount_change = new_hires - terminations
        adjusted_monthly_salary = simulated_salary + (Decimal(str(net_headcount_change)) * avg_sal * inc_factor)
        adjusted_monthly_benefits = base_monthly_benefits + (Decimal(str(net_headcount_change)) * avg_ben)
        adjusted_charges = adjusted_monthly_salary * Decimal('0.35')
        
        simulated_monthly_payroll = adjusted_monthly_salary
        simulated_monthly_total = adjusted_monthly_salary + adjusted_monthly_benefits + adjusted_charges
        simulated_annual_cost = simulated_monthly_total * Decimal('12')

    cost_diff = simulated_annual_cost - base_annual_cost

    context = {
        'base_headcount': base_headcount,
        'base_monthly_payroll': base_monthly_total,
        'simulated_headcount': simulated_headcount,
        'simulated_monthly_payroll': simulated_monthly_total,
        'simulated_annual_cost': simulated_annual_cost,
        'cost_diff': cost_diff,
        'salary_increase': salary_increase,
        'new_hires': new_hires,
        'terminations': terminations,
    }
    return render(request, 'hr_budget/simulator.html', context)
