# KI Lab SS25 - Data challenge Oerlikon

## Pattern in sales data

Are there any pattern in the sales data that would allow to better forecast / plan?

Data consits out of sales order lines, including:

- Industry
- Product_Family
- CHF: price in CHF
- PC: quanity of tools in the order line
- fill_rate:  occupation of the order line in a (reference) coater
- Diameter max (mm)
- Length (mm)
- Width total (mm)
- order_date
- tool_type: tool type, e.g. Drill
- Customer_id
- coating_id: coating type, e.g. Alcrona Pro, different coatings have different properties consist out of different materials


Some assumptions:

- one coater can do 2-3 batches a day
- one operator can operate 2 machines
- tools should be returned within 5 days
- only the same coating IDs can come into the same machine