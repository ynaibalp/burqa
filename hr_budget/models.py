from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    LEVEL_CHOICES = [
        ('Junior', 'Júnior'),
        ('Pleno', 'Pleno'),
        ('Senior', 'Sênior'),
        ('Management', 'Gestão/Diretoria'),
    ]
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Pleno')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} ({self.level}) - {self.department.name}"

class Employee(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Ativo'),
        ('Vacation', 'Férias'),
        ('Terminated', 'Desligado'),
    ]
    name = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='employees')
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    benefits_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1200.00)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.name} - {self.position.title}"

    @property
    def total_cost(self):
        # Salary + Benefits + Estimated 35% taxes/charges (INSS, FGTS, Provisões)
        charges = self.salary * 0.35
        return self.salary + self.benefits_cost + charges

class BudgetExpense(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    category = models.CharField(max_length=100) # e.g., 'Recrutamento', 'Treinamento', 'Eventos'
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField() # 1-12
    year = models.IntegerField(default=2026)

    def __str__(self):
        return f"{self.category} - R$ {self.amount} ({self.month}/{self.year})"
