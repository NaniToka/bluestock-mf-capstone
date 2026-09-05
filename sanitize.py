import re
for fname in ["scripts/generate_report.py", "scripts/generate_presentation.py"]:
    try:
        with open(fname, "r") as f:
            c = f.read()

        c = re.sub(r'\(F001\)', '', c)
        c = re.sub(r'F001 \(Bluestock Large Cap\)', 'The top equity large-cap fund', c)
        c = re.sub(r'F001 and F007 \(both Large Cap\)', 'the top large cap funds', c)
        c = re.sub(r'for F001:', 'for the top fund:', c)
        c = re.sub(r'Debt funds \(F004, F005, F010\)', 'Debt funds', c)
        c = re.sub(r'F001 achieved', 'The top fund achieved', c)
        c = re.sub(r'Conservative: F010.*', 'Conservative: Debt and Liquid funds', c)
        c = re.sub(r'Moderate: F006.*', 'Moderate: Hybrid and Balanced funds', c)
        c = re.sub(r'Aggressive: F001.*', 'Aggressive: Large Cap, Mid Cap, and Small Cap funds', c)
        c = re.sub(r'Bluestock Large Cap Fund \(F001\)', 'The top fund', c)
        c = re.sub(r'Hybrid funds \(F006, F009\)', 'Hybrid funds', c)
        c = re.sub(r'Apex Balanced Advantage \(F009\) showed negative 1Y CAGR \(–17.35%\)', 'Underperforming funds showed negative 1Y CAGR', c)
        
        # ppt
        c = re.sub(r'F001 = \{ab\[ab\.fund_id==\'F001\'\]\.alpha_ann\.values\[0\]:\.4f\}', 'Top Fund = {ab[\'alpha\'].max():.4f}', c)
        c = re.sub(r'F001 \(Large Cap\) and F007 \(Bluechip\)', 'Top Large Cap funds', c)
        c = re.sub(r'F003 Flexi Cap at \{sc\[sc\.fund_id==\'F003\'\]\.max_drawdown_pct\.values\[0\]:\.1f\}', 'Worst at {sc[\'max_drawdown_pct\'].min():.1f}', c)
        c = re.sub(r'F010 Gilt at \{sc\[sc\.fund_id==\'F010\'\]\.max_drawdown_pct\.values\[0\]:\.1f\}', 'Best at {sc[\'max_drawdown_pct\'].max():.1f}', c)
        c = re.sub(r'F001 \(Bluestock Large Cap\): #1 fund', 'Top #1 fund', c)
        c = re.sub(r'Increase marketing spend on F001', 'Increase marketing spend on top fund', c)
        c = re.sub(r'Review F009 \(Apex Balanced\): –17.35% 1Y CAGR in 2025', 'Review underperforming funds with negative CAGR', c)
        
        with open(fname, "w") as f:
            f.write(c)
    except FileNotFoundError:
        pass
