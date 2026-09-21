import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hr_budget.models import Department, Position, Employee, BudgetExpense

class Command(BaseCommand):
    help = 'Popula o banco de dados com departamentos, cargos e ~150 funcionários fictícios para o sistema Burqa.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando o povoamento (seed) do Burqa...")

        # 1. Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@burqa.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("Superusuário criado: admin / admin123"))

        # 2. Departments
        depts_data = [
            ("Tecnologia", "TEC"),
            ("Vendas", "VEN"),
            ("Marketing", "MKT"),
            ("Operações", "OPS"),
            ("Recursos Humanos", "RHU"),
            ("Financeiro", "FIN"),
        ]
        
        departments = {}
        for name, code in depts_data:
            dept, _ = Department.objects.get_or_create(code=code, defaults={'name': name})
            departments[code] = dept

        # 3. Positions per department
        positions_data = {
            "TEC": [
                ("Desenvolvedor Júnior", "Junior", 4500.00),
                ("Desenvolvedor Pleno", "Pleno", 8500.00),
                ("Desenvolvedor Sênior", "Senior", 14000.00),
                ("Tech Lead", "Management", 18500.00),
            ],
            "VEN": [
                ("Analista de Vendas Jr", "Junior", 3500.00),
                ("Executivo de Contas", "Pleno", 7000.00),
                ("Key Account Manager", "Senior", 11000.00),
                ("Gerente de Vendas", "Management", 16000.00),
            ],
            "MKT": [
                ("Assistente de Marketing", "Junior", 3200.00),
                ("Analista de Marketing Pl", "Pleno", 6000.00),
                ("Analista de Marketing Sr", "Senior", 9500.00),
                ("Head de Marketing", "Management", 15000.00),
            ],
            "OPS": [
                ("Assistente de Operações", "Junior", 2800.00),
                ("Analista de Operações Pl", "Pleno", 5500.00),
                ("Supervisor de Operações", "Senior", 8800.00),
                ("Diretor de Operações", "Management", 17000.00),
            ],
            "RHU": [
                ("Analista de DP Jr", "Junior", 3300.00),
                ("Analista de RH Pleno", "Pleno", 6200.00),
                ("Business Partner Sênior", "Senior", 10500.00),
                ("Gerente de RH", "Management", 15500.00),
            ],
            "FIN": [
                ("Assistente Financeiro", "Junior", 3400.00),
                ("Analista Financeiro Pl", "Pleno", 6500.00),
                ("Controlador Financeiro", "Senior", 12000.00),
                ("CFO / Diretor Financeiro", "Management", 20000.00),
            ],
        }

        positions = {}
        for code, pos_list in positions_data.items():
            dept = departments[code]
            positions[code] = []
            for title, level, salary in pos_list:
                pos, _ = Position.objects.get_or_create(
                    title=title,
                    department=dept,
                    defaults={'level': level, 'base_salary': salary}
                )
                positions[code].append(pos)

        # Clear existing employees to prevent duplication on re-run
        Employee.objects.all().delete()

        first_names = [
            "Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena", 
            "Igor", "Juliana", "Lucas", "Mariana", "Nicolas", "Patrícia", "Rafael", "Camila",
            "Thiago", "Vanessa", "Rodrigo", "Larissa", "Mateus", "Beatriz", "Gustavo", "Amanda",
            "Felipe", "Letícia", "Marcos", "Jéssica", "Diego", "Natália", "Leonardo", "Bianca"
        ]
        last_names = [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
            "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
            "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade"
        ]

        # 4. Generate ~150 employees
        employee_count = 159
        created_count = 0

        for i in range(1, employee_count + 1):
            name = f"{random.choice(first_names)} {random.choice(last_names)} {random.choice(last_names)}"
            cpf = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
            
            # Ensure unique CPF
            while Employee.objects.filter(cpf=cpf).exists():
                cpf = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"

            dept_code = random.choice(list(departments.keys()))
            dept = departments[dept_code]
            pos = random.choice(positions[dept_code])

            # Vary salary slightly around base salary (+/- 10%)
            variation = random.uniform(0.9, 1.15)
            salary = round(float(pos.base_salary) * variation, 2)
            benefits = round(random.choice([1000.00, 1200.00, 1500.00]), 2)

            # Hire date between 2020 and 2025
            start_date = date(2020, 1, 1)
            end_date = date(2025, 12, 31)
            days_between = (end_date - start_date).days
            hire_date = start_date + timedelta(days=random.randint(0, days_between))

            status = random.choices(['Active', 'Vacation', 'Terminated'], weights=[85, 10, 5])[0]

            Employee.objects.create(
                name=name,
                cpf=cpf,
                email=f"funcionario{i}@burqa.com",
                department=dept,
                position=pos,
                salary=salary,
                benefits_cost=benefits,
                hire_date=hire_date,
                status=status
            )
            created_count += 1

        # 5. Seed Budget Expenses
        BudgetExpense.objects.all().delete()
        expense_categories = ['Recrutamento & Seleção', 'Treinamento & Desenvolvimento', 'Eventos & Cultura', 'Licenças de Software']
        for month in range(1, 13):
            for dept in departments.values():
                BudgetExpense.objects.create(
                    department=dept,
                    category=random.choice(expense_categories),
                    description=f"Despesa operacional mensal - {dept.name}",
                    amount=round(random.uniform(5000.00, 25000.00), 2),
                    month=month,
                    year=2026
                )

        self.stdout.write(self.style.SUCCESS(f"Sucesso! {created_count} funcionários e despesas orçamentárias geradas para o projeto Burqa."))
