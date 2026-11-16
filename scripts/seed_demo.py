"""Seed demo data for SupportIQ (e-commerce support organization)."""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select
from app.database.session import AsyncSessionLocal, engine, Base
from app.models.organization import Organization, OrganizationSettings
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.knowledge import KnowledgeArticle, KnowledgeDocument
from app.core.security import get_password_hash


PERMISSIONS = [
    ("tickets.view", "View Tickets", "tickets"),
    ("tickets.create", "Create Tickets", "tickets"),
    ("tickets.update", "Update Tickets", "tickets"),
    ("tickets.assign", "Assign Tickets", "tickets"),
    ("tickets.close", "Close Tickets", "tickets"),
    ("customers.view", "View Customers", "customers"),
    ("customers.manage", "Manage Customers", "customers"),
    ("agents.manage", "Manage Agents", "agents"),
    ("knowledge.manage", "Manage Knowledge Base", "knowledge"),
    ("ai.manage", "Manage AI Settings", "ai"),
    ("analytics.view", "View Analytics", "analytics"),
    ("organization.manage", "Manage Organization", "organization"),
    ("users.manage", "Manage Users", "users"),
    ("audit.view", "View Audit Logs", "audit"),
]

ROLES = {
    "Super Admin": [p[0] for p in PERMISSIONS],
    "Organization Admin": [p[0] for p in PERMISSIONS if p[0] != "audit.view"],
    "Support Manager": [
        "tickets.view", "tickets.create", "tickets.update", "tickets.assign", "tickets.close",
        "customers.view", "customers.manage", "agents.manage", "knowledge.manage",
        "analytics.view",
    ],
    "Support Agent": [
        "tickets.view", "tickets.create", "tickets.update", "tickets.close",
        "customers.view",
    ],
    "Customer": ["tickets.view", "tickets.create", "customers.view"],
    "Analyst": ["tickets.view", "customers.view", "analytics.view", "audit.view"],
}


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Organization
        result = await db.execute(select(Organization).where(Organization.slug == "demo-ecommerce"))
        org = result.scalar_one_or_none()
        if not org:
            org = Organization(
                name="Demo E-Commerce Support",
                slug="demo-ecommerce",
                description="Sample e-commerce organization for SupportIQ demos",
                timezone="UTC",
            )
            db.add(org)
            await db.flush()
            db.add(OrganizationSettings(organization_id=org.id, ai_enabled=True, chatbot_enabled=True))
            print(f"Created organization: {org.slug}")

        # Permissions & Roles
        perm_map = {}
        for codename, name, module in PERMISSIONS:
            result = await db.execute(select(Permission).where(Permission.codename == codename))
            p = result.scalar_one_or_none()
            if not p:
                p = Permission(codename=codename, name=name, module=module)
                db.add(p)
                await db.flush()
            perm_map[codename] = p

        role_map = {}
        for role_name, perms in ROLES.items():
            result = await db.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name=role_name, description=f"{role_name} role", is_system=True)
                db.add(role)
                await db.flush()
                for code in perms:
                    if code in perm_map:
                        db.add(RolePermission(role_id=role.id, permission_id=perm_map[code].id))
            role_map[role_name] = role

        # Users
        users_data = [
            ("admin@demo.com", "Admin User", "Super Admin", "Admin123!"),
            ("manager@demo.com", "Support Manager", "Support Manager", "Manager123!"),
            ("agent1@demo.com", "Alice Agent", "Support Agent", "Agent123!"),
            ("agent2@demo.com", "Bob Agent", "Support Agent", "Agent123!"),
            ("customer@demo.com", "Jane Customer", "Customer", "Customer123!"),
            ("analyst@demo.com", "Data Analyst", "Analyst", "Analyst123!"),
        ]
        user_map = {}
        for email, full_name, role_name, password in users_data:
            result = await db.execute(
                select(User).where(User.email == email, User.organization_id == org.id)
            )
            u = result.scalar_one_or_none()
            if not u:
                u = User(
                    organization_id=org.id,
                    email=email,
                    full_name=full_name,
                    hashed_password=get_password_hash(password),
                    is_active=True,
                    is_email_verified=True,
                    is_superuser=(role_name == "Super Admin"),
                )
                db.add(u)
                await db.flush()
                db.add(UserRole(user_id=u.id, role_id=role_map[role_name].id))
                print(f"Created user: {email} / {password}")
            user_map[email] = u

        # Customers
        customers_data = [
            ("John Smith", "john.smith@example.com", "Acme Corp", "business"),
            ("Sarah Johnson", "sarah.j@example.com", None, "individual"),
            ("Mike Chen", "mike.chen@example.com", "TechStart Inc", "business"),
            ("Emily Davis", "emily.d@example.com", None, "individual"),
            ("Robert Wilson", "robert.w@example.com", "Global Traders", "business"),
        ]
        customer_map = {}
        for name, email, company, ctype in customers_data:
            result = await db.execute(
                select(Customer).where(Customer.email == email, Customer.organization_id == org.id)
            )
            c = result.scalar_one_or_none()
            if not c:
                c = Customer(
                    organization_id=org.id,
                    full_name=name,
                    email=email,
                    company=company,
                    customer_type=ctype,
                    account_status="active",
                    tags=["vip"] if company else ["retail"],
                )
                db.add(c)
                await db.flush()
            customer_map[email] = c

        # Sample tickets
        tickets_data = [
            (customer_map["john.smith@example.com"], "Order not received", "I ordered #ORD-10045 three weeks ago and still have no tracking update.", "high", "delivery_delay"),
            (customer_map["sarah.j@example.com"], "Request refund for damaged item", "Product arrived broken. Order #ORD-10089. I want a full refund.", "high", "refund_request"),
            (customer_map["mike.chen@example.com"], "Cannot log into my account", "Password reset emails are not arriving. Account email: mike.chen@example.com", "medium", "login_issue"),
            (customer_map["emily.d@example.com"], "Where is my package?", "Tracking number TRK998877 shows no movement for 5 days.", "medium", "order_tracking"),
            (customer_map["robert.w@example.com"], "Wrong item received", "I ordered a blue widget but received a red one. Order #ORD-10102.", "high", "product_complaint"),
        ]
        for cust, subject, desc, priority, intent in tickets_data:
            result = await db.execute(
                select(Ticket).where(
                    Ticket.organization_id == org.id,
                    Ticket.subject == subject,
                )
            )
            if result.scalar_one_or_none() is None:
                t = Ticket(
                    organization_id=org.id,
                    customer_id=cust.id,
                    ticket_number=f"TKT-DEMO-{uuid.uuid4().hex[:6].upper()}",
                    subject=subject,
                    description=desc,
                    priority=priority,
                    status=TicketStatus.OPEN.value,
                    source_channel="portal",
                    intent=intent,
                    category="Orders" if "order" in intent or "delivery" in intent else "Support",
                    ai_classified=True,
                    ai_confidence=0.82,
                    assigned_agent_id=user_map["agent1@demo.com"].id,
                )
                db.add(t)

        # Knowledge articles
        articles = [
            ("Refund Policy", "refund-policy",
             "Eligible items may be refunded within 30 days of delivery if they are unused and in original packaging. "
             "To request a refund, provide your order number. Refunds are processed within 5-7 business days after approval. "
             "Digital goods and personalized items are non-refundable."),
            ("Shipping & Tracking FAQ", "shipping-tracking",
             "Standard shipping takes 3-7 business days. Express shipping takes 1-2 business days. "
             "You will receive a tracking number via email once your order ships. "
             "If tracking shows no movement for more than 5 business days, contact support with your order number."),
            ("Account Recovery Guide", "account-recovery",
             "To recover your account: 1) Click Forgot Password on the login page. 2) Enter your registered email. "
             "3) Check your inbox (and spam folder) for a reset link valid for 24 hours. "
             "If you do not receive the email, contact support with proof of account ownership."),
            ("Return Policy", "return-policy",
             "Returns are accepted within 30 days. Items must be in original condition. "
             "Start a return from your order history page. A prepaid label will be provided for eligible returns. "
             "Refunds are issued after the warehouse inspects the returned item."),
            ("Warranty Information", "warranty-info",
             "Most products carry a 12-month manufacturer warranty covering defects in materials and workmanship. "
             "Warranty does not cover damage from misuse or normal wear. "
             "Contact support with your order number and a description of the defect to initiate a warranty claim."),
        ]
        for title, slug, content in articles:
            result = await db.execute(
                select(KnowledgeArticle).where(
                    KnowledgeArticle.organization_id == org.id,
                    KnowledgeArticle.slug == slug,
                )
            )
            if result.scalar_one_or_none() is None:
                db.add(KnowledgeArticle(
                    organization_id=org.id,
                    title=title,
                    slug=slug,
                    content=content,
                    summary=content[:150],
                    category="Policies",
                    is_published=True,
                    is_approved=True,
                    tags=["policy", "faq"],
                ))

        await db.commit()
        print("\n✅ Demo data seeded successfully.")
        print("\nDemo credentials:")
        print("  Admin:    admin@demo.com / Admin123!")
        print("  Manager:  manager@demo.com / Manager123!")
        print("  Agent:    agent1@demo.com / Agent123!")
        print("  Customer: customer@demo.com / Customer123!")


if __name__ == "__main__":
    asyncio.run(seed())