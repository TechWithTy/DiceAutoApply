# Streamlit App Setup Guide: Authentication, Login/Signup, and Credit Buying

## Overview

This guide documents how to set up authentication, login/signup functionality, and credit buying via Stripe callbacks in your Streamlit application. The setup supports both Streamlit native implementation and integration with React or other GUI frameworks for a more polished user experience.

## Technology Stack

- **Frontend**: Streamlit (Python), React/Next.js (TypeScript)
- **Backend**: FastAPI (Python), PostgreSQL
- **Payments**: Stripe
- **Authentication**: Custom token-based auth with SaaS API integration

## Architecture

The application uses a decoupled architecture:
- **Streamlit App**: Primary UI for job application automation
- **SaaS API**: Handles authentication, user management, and entitlements
- **Stripe Integration**: Manages payment processing and credit allocation

## Setting Up Authentication

### 1. Streamlit Authentication Setup

The Streamlit app supports two authentication methods:

#### Dice Email/Password Authentication (Local)

```python
# streamlit_app/ui_auth.py
def render_login() -> bool:
    """Render login form for Dice credentials."""
    st.header("Login")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Dice Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    
    if submitted and validate_credentials(email, password):
        set_credentials(Credentials(email=email, password=password))
        return True
    return False
```

#### SaaS Provider Authentication (Production)

```python
# streamlit_app/ui_saas.py
def render_login_prompt() -> None:
    """Render login link to external SaaS provider."""
    url = build_login_url()
    st.warning("You must log in to continue.")
    st.markdown(f"[Login Here]({url})")

def ensure_token_from_query() -> Optional[str]:
    """Extract and store auth token from URL query parameters."""
    token = st.query_params.get("token")
    if token:
        set_auth_token(token)
    return get_auth_token()
```

### 2. Backend Authentication API

Set up authentication endpoints in your FastAPI backend:

```python
# Backend authentication routes
@app.post("/login")
async def login(request: LoginRequest):
    # Validate credentials
    # Generate JWT token
    # Return token and redirect URL
    pass

@app.get("/entitlements")
async def get_entitlements(token: str = Depends(verify_token)):
    # Return user credits and entitlements
    return {"credits": user.credits, "features": user.features}
```

## Integrating Credit Buying via Stripe

### 1. Stripe Checkout Setup

Install Stripe Python SDK:
```bash
pip install stripe
```

Create Stripe checkout session in your backend:

```python
# payment/stripe_service.py
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(user_id: str, credit_amount: int) -> str:
    """Create Stripe checkout session for credit purchase."""
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'{credit_amount} Credits',
                },
                'unit_amount': 100 * credit_amount,  # $1 per credit
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"{os.getenv('APP_BASE_URL')}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.getenv('APP_BASE_URL')}/cancel",
        metadata={
            'user_id': user_id,
            'credit_amount': credit_amount
        }
    )
    return session.url
```

### 2. Webhook Handler for Payment Confirmation

```python
# payment/webhook_handler.py
@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await process_successful_payment(session)
    
    return {"status": "success"}

async def process_successful_payment(session):
    """Process successful payment and allocate credits."""
    user_id = session['metadata']['user_id']
    credit_amount = int(session['metadata']['credit_amount'])
    
    # Allocate credits to user
    await allocate_credits_to_user(user_id, credit_amount)
    
    # Send confirmation email
    await send_credit_confirmation_email(user_id, credit_amount)
```

### 3. Streamlit Credit Buying Integration

Add credit buying UI to your Streamlit app:

```python
# streamlit_app/ui_credits.py
def render_credit_purchase() -> None:
    """Render credit purchase interface."""
    st.header("Buy Credits")
    
    credit_options = [10, 25, 50, 100]
    selected_credits = st.selectbox(
        "Select Credit Package",
        credit_options,
        format_func=lambda x: f"{x} Credits - ${x}"
    )
    
    if st.button(f"Purchase {selected_credits} Credits"):
        token = get_auth_token()
        if not token:
            st.error("Please log in first")
            return
        
        # Call API to create checkout session
        checkout_url = create_checkout_session(token, selected_credits)
        if checkout_url:
            st.markdown(f"[Complete Purchase]({checkout_url})")
        else:
            st.error("Failed to create checkout session")
```

## Callbacks and Payment Processing

### 1. Success Callback Handling

After successful payment, redirect users back to your app:

```python
# streamlit_app/ui_saas.py
def handle_payment_success() -> None:
    """Handle successful payment callback."""
    session_id = st.query_params.get("session_id")
    if session_id:
        # Verify payment and update credits
        credits = verify_and_update_credits(session_id)
        if credits:
            st.success(f"Payment successful! {credits} credits added to your account.")
            st.balloons()
        else:
            st.error("Payment verification failed")
```

### 2. Credit Verification API

```python
# Backend API endpoint
@app.get("/verify-payment/{session_id}")
async def verify_payment(session_id: str, token: str = Depends(verify_token)):
    """Verify payment and return updated credit balance."""
    # Retrieve session from Stripe
    # Update user credits if payment is valid
    # Return new credit balance
    pass
```

## Usage in React or Nicer GUIs

For a more polished user experience, integrate with React:

### 1. React Frontend Setup

Create a React component for authentication:

```typescript
// src/components/AuthProvider.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  token: string | null;
  credits: number;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  purchaseCredits: (amount: number) => Promise<string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [credits, setCredits] = useState(0);
  
  // Initialize from localStorage or URL params
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
      localStorage.setItem('authToken', tokenParam);
      // Fetch user credits
      fetchCredits(tokenParam);
    } else {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        setToken(storedToken);
        fetchCredits(storedToken);
      }
    }
  }, []);
  
  const login = async (email: string, password: string) => {
    // Call backend login API
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const { token } = await response.json();
      setToken(token);
      localStorage.setItem('authToken', token);
      await fetchCredits(token);
    } else {
      throw new Error('Login failed');
    }
  };
  
  const fetchCredits = async (authToken: string) => {
    const response = await fetch('/api/entitlements', {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    if (response.ok) {
      const data = await response.json();
      setCredits(data.credits);
    }
  };
  
  const purchaseCredits = async (amount: number): Promise<string> => {
    const response = await fetch('/api/create-checkout', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ credit_amount: amount })
    });
    
    if (response.ok) {
      const { checkout_url } = await response.json();
      return checkout_url;
    } else {
      throw new Error('Failed to create checkout session');
    }
  };
  
  const logout = () => {
    setToken(null);
    setCredits(0);
    localStorage.removeItem('authToken');
  };
  
  return (
    <AuthContext.Provider value={{ token, credits, login, logout, purchaseCredits }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 2. Credit Purchase Component

```typescript
// src/components/CreditPurchase.tsx
import React, { useState } from 'react';
import { useAuth } from './AuthProvider';

const CreditPurchase: React.FC = () => {
  const { purchaseCredits, credits } = useAuth();
  const [loading, setLoading] = useState(false);
  
  const handlePurchase = async (amount: number) => {
    setLoading(true);
    try {
      const checkoutUrl = await purchaseCredits(amount);
      window.location.href = checkoutUrl; // Redirect to Stripe
    } catch (error) {
      console.error('Purchase failed:', error);
      // Handle error
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="credit-purchase">
      <h2>Current Credits: {credits}</h2>
      <div className="purchase-options">
        {[10, 25, 50, 100].map(amount => (
          <button
            key={amount}
            onClick={() => handlePurchase(amount)}
            disabled={loading}
          >
            Buy {amount} Credits (${amount})
          </button>
        ))}
      </div>
    </div>
  );
};

export default CreditPurchase;
```

## Best Practices

1. **Security**:
   - Never expose Stripe secret keys in client-side code
   - Use HTTPS for all API communications
   - Validate webhooks with proper signature verification

2. **Error Handling**:
   - Implement retry logic for failed API calls
   - Provide clear error messages to users
   - Log errors for debugging

3. **User Experience**:
   - Show loading states during API calls
   - Provide clear feedback for successful/failed operations
   - Use progressive enhancement for better accessibility

4. **Testing**:
   - Test payment flows in Stripe's test mode
   - Mock external API calls in unit tests
   - Test error scenarios and edge cases

## Deployment Considerations

1. **Environment Variables**:
   ```bash
   # .env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   SAAS_API_URL=https://your-api.com
   APP_BASE_URL=https://your-app.com
   ```

2. **CORS Configuration**:
   - Configure CORS in FastAPI for cross-origin requests from React
   - Set up proper content security policies

3. **Database Schema**:
   ```sql
   -- User credits table
   CREATE TABLE user_credits (
     user_id UUID PRIMARY KEY,
     credits INTEGER DEFAULT 0,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

This setup provides a robust foundation for authentication and credit-based payments in your job application automation tool, with flexibility for both Streamlit and React interfaces.
