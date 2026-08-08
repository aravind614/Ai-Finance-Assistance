from pydantic import BaseModel, Field


class FinancialResearch(BaseModel):
    company: str | None = Field(
        default=None,
        description="Company name"
    )

    quarter: str | None = Field(
        default=None,
        description="Financial quarter or reporting period"
    )

    revenue: float | None = Field(
        default=None,
        description="Current-period revenue in millions"
    )

    previous_revenue: float | None = Field(
        default=None,
        description="Comparable prior-period revenue in millions"
    )

    net_income: float | None = Field(
        default=None,
        description="Current-period net income in millions"
    )

    previous_net_income: float | None = Field(
        default=None,
        description="Comparable prior-period net income in millions"
    )

    eps: float | None = Field(
        default=None,
        description="Current-period diluted EPS"
    )

    previous_eps: float | None = Field(
        default=None,
        description="Comparable prior-period diluted EPS"
    )

    revenue_growth: float | None = Field(
        default=None,
        description="Revenue growth percentage calculated by Python"
    )

    net_income_growth: float | None = Field(
        default=None,
        description="Net income growth percentage calculated by Python"
    )

    summary: str | None = Field(
        default=None,
        description="Brief financial performance summary"
    )

    risks: list[str] | None = Field(
        default=None,
        description="Important financial or business risks"
    )

    sources: list[str] = Field(
        default_factory=list,
        description="Source URLs"
    )


class InvestmentReport(BaseModel):
    company: str = Field(description="Name of the company researched")
    company_overview: str = Field(description="Detailed overview of the company's business model and operations")
    industry: str = Field(description="Overview of the industry and sector the company operates in")
    business_model: str = Field(description="How the company makes money, major revenue sources, and value proposition")
    latest_news: list[str] = Field(default_factory=list, description="Summary of latest financial or company news")
    strengths: list[str] = Field(default_factory=list, description="Key business strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Key business weaknesses")
    financial_highlights: str = Field(description="Revenue, Net Income, growth rates, margins, and key financial ratios")
    growth_opportunities: list[str] = Field(default_factory=list, description="Potential avenues for future growth")
    potential_risks: list[str] = Field(default_factory=list, description="Potential risks and warning factors")
    investment_summary: str = Field(description="Final summary and investment recommendation (e.g. Buy/Hold/Sell decision and rationale)")


class InvestorProfile(BaseModel):
    name: str = Field(default="Valued Client", description="Investor/Client name")
    investment_interests: str = Field(default="", description="Specific interests (e.g., tech growth stocks, dividends)")
    preferred_industries: list[str] = Field(default_factory=list, description="Industries of interest")
    risk_profile: str = Field(default="Moderate", description="Risk profile: Low, Moderate, High")
    frequently_researched: list[str] = Field(default_factory=list, description="List of frequently researched companies")


class RouteDecision(BaseModel):
    route: str = Field(description="The destination route/agent: 'news', 'pdf_rag', 'research', 'compare', 'email', 'calculate', 'memory', or 'general'")
    explanation: str = Field(description="Explanation of why this route was selected")

