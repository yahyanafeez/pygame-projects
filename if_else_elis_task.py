name=input("enter your name:")
unit=int(input("unit consumed in wkh:"))
if unit <= 100:
    rate=1.5
elif unit <=200:
    rate=2.5
elif unit <=300:
    rate=4.0
else:
    rate=6.0
calculate_total_bill=unit*rate
add_tax=5%+calculate_total_bill
final_bill=calculate_total_bill+add_tax
print(f"coustmer name:{name}")
print(f"unit consumed in kwh:{unit}")
print(f"your bill:{calculate_total_bill}")
print(f"your bill + 5% of tax:{add_tax}")
print(f"your final bill:{final_bill}")


