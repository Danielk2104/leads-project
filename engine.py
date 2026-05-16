import pandas as pd

def leads_transform(df):
   
    df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce').fillna(0)
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors='coerce').fillna(0)
    
    num_leads = len(df)
    if num_leads == 0:
        return df

# Lead score - Features

    df["ReviewsScore"] = df["Reviews"].rank(pct=True) * 100
    df["RatingScore"] = df["Rating"].rank(pct=True) * 100
    df["CompetitiveRaw"] = (0.6 * df["ReviewsScore"]/100) + (0.4 * df["RatingScore"]/100)
    df["CompetitiveScore"] = (df["CompetitiveRaw"] * 50).round(2)
    
# Lead score - Modifiers
    
    def modifiers(row):
        points = 0 
        reasons = []
        if not row.get("Website") or str(row["Website"]).lower() in ['n/a','none','nan','']:
            reasons.append("🚫 No website found: Potential sales opportunity!")
        else:
            base_web = 25
            points += base_web
            reasons.append(f"🌐 Has Website: Established business +{base_web} points")
        
        if not row.get("Phone") or str(row["Phone"]).lower() in ['n/a','none','nan','']:
            reasons.append("📵 No Phone number found: Harder to contact")
        else:
            base_phone = 25
            points += 25
            reasons.append(f"📱 Has phone number: Easier to contact + {base_phone} points ")
        return pd.Series([points,reasons])
    
    df[["ModifierScore","ScoreReasons"]] = df.apply(modifiers,axis=1)
    df["LeadScore"] = (df["CompetitiveScore"] + df["ModifierScore"]).round(2)
    df = df.sort_values(by="LeadScore", ascending=False).reset_index(drop=True)
    
    def get_color(score):
        if score >= 80: return [34,139,34,200]
        if score >= 50: return [265,165,0,200]
        return [220,20,60,200]
    
    df['colour'] = df['LeadScore'].apply(get_color)

    return df
