from apps.portfolio.models import Portfolio


def get_or_create_default_portfolio(user) -> Portfolio:
    portfolio = Portfolio.objects.for_user(user).filter(is_default=True).first()
    if portfolio:
        return portfolio

    return Portfolio.objects.create(
        user=user,
        name="Hoofdportefeuille",
        is_default=True,
    )
