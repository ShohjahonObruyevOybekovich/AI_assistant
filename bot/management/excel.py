import pandas as pd
from django.core.management.base import BaseCommand
from bot.models import User, Installment, Category
from datetime import datetime

class Command(BaseCommand):
    help = 'Upload users and installments from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name=0)

            for _, row in df.iterrows():
                # Process User
                phone = str(row['Tel raqami']).replace(',', '').strip()  # Clean phone format
                user, created = User.objects.get_or_create(
                    phone=phone,
                    defaults={
                        'full_name': row["To'liq ism familiyasi"],
                    }
                )

                # Process Category (create a default category if none exists)
                category_name = "Default"  # Assign a default category
                category, _ = Category.objects.get_or_create(name=category_name)

                # Parse and clean dates
                start_date = datetime.strptime(row['rasrochka boshlangan oy'], '%d,%m,%Y').date() if pd.notna(row['rasrochka boshlangan oy']) else None
                next_payment_date = datetime.strptime(row['kelasi to\'lov muddati'], '%d,%m,%Y').date() if pd.notna(row['kelasi to\'lov muddati']) else None

                # Process Installment
                Installment.objects.create(
                    user=user,
                    category=category,
                    product=row['maxsulotlar'],
                    price=row['tan narxi'],
                    starter_payment=row['boshlang\'ich to\'lov'],
                    payment_months=row['rasrochka oylari'],
                    additional_fee_percentage=row['qo\'shilgan foiz'],
                    start_date=start_date,
                    next_payment_dates=next_payment_date,
                    status='COMPLETED' if 'yopilgan' in str(row['jami to\'langan to\'lovlar']).lower() else 'ACTIVE'
                )

            self.stdout.write(self.style.SUCCESS('Data uploaded successfully'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error uploading data: {e}'))
