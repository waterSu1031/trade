from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.database.models import Position as DBPosition
from app.models.position import PositionResponse, PositionCreate, PositionUpdate
from app.services.ibkr_service import ibkr_service

router = APIRouter()

@router.get("/", response_model=List[PositionResponse])
async def get_positions(
    active_only: bool = Query(True),
    symbol: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all positions with optional filtering"""
    query = db.query(DBPosition)
    
    if active_only:
        query = query.filter(DBPosition.is_active == True)
    
    if symbol:
        query = query.filter(DBPosition.symbol == symbol)
    
    positions = query.order_by(DBPosition.symbol).all()
    return positions

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: int, db: Session = Depends(get_db)):
    """Get a specific position by ID"""
    position = db.query(DBPosition).filter(DBPosition.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@router.post("/", response_model=PositionResponse)
async def create_position(position: PositionCreate, db: Session = Depends(get_db)):
    """Create a new position record"""
    db_position = DBPosition(**position.dict())
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    return db_position

@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: int,
    position_update: PositionUpdate,
    db: Session = Depends(get_db)
):
    """Update a position record"""
    db_position = db.query(DBPosition).filter(DBPosition.id == position_id).first()
    if not db_position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    update_data = position_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_position, field, value)
    
    db.commit()
    db.refresh(db_position)
    return db_position

@router.get("/live/current")
async def get_live_positions():
    """Get current positions from IBKR"""
    try:
        positions = await ibkr_service.get_positions()
        return [
            {
                "symbol": pos.contract.symbol,
                "position": pos.position,
                "avgCost": pos.avgCost,
                "marketPrice": pos.marketPrice,
                "marketValue": pos.marketValue,
                "unrealizedPNL": pos.unrealizedPNL,
                "realizedPNL": pos.realizedPNL,
                "currency": pos.contract.currency,
                "exchange": pos.contract.exchange
            }
            for pos in positions
            if pos.position != 0  # Only show non-zero positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching live positions: {str(e)}")

@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get portfolio summary from IBKR"""
    try:
        portfolio_items = await ibkr_service.get_portfolio()
        account_summary = await ibkr_service.get_account_summary()
        
        total_market_value = sum(item.marketValue for item in portfolio_items)
        total_unrealized_pnl = sum(item.unrealizedPNL for item in portfolio_items)
        total_realized_pnl = sum(item.realizedPNL for item in portfolio_items)
        
        return {
            "total_positions": len([item for item in portfolio_items if item.position != 0]),
            "total_market_value": total_market_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "net_liquidation": account_summary.get("NetLiquidation", {}).get("value", 0),
            "total_cash": account_summary.get("TotalCashValue", {}).get("value", 0),
            "buying_power": account_summary.get("BuyingPower", {}).get("value", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio summary: {str(e)}")

@router.post("/sync")
async def sync_positions_from_ibkr(db: Session = Depends(get_db)):
    """Sync positions from IBKR to database"""
    try:
        live_positions = await ibkr_service.get_positions()
        
        synced_count = 0
        for pos in live_positions:
            if pos.position == 0:
                continue
                
            # Check if position exists
            db_position = db.query(DBPosition).filter(
                DBPosition.symbol == pos.contract.symbol
            ).first()
            
            if db_position:
                # Update existing position
                db_position.quantity = pos.position
                db_position.avg_cost = pos.avgCost
                db_position.market_price = pos.marketPrice
                db_position.market_value = pos.marketValue
                db_position.unrealized_pnl = pos.unrealizedPNL
                db_position.realized_pnl = pos.realizedPNL
                db_position.is_active = True
            else:
                # Create new position
                db_position = DBPosition(
                    symbol=pos.contract.symbol,
                    quantity=pos.position,
                    avg_cost=pos.avgCost,
                    market_price=pos.marketPrice,
                    market_value=pos.marketValue,
                    unrealized_pnl=pos.unrealizedPNL,
                    realized_pnl=pos.realizedPNL,
                    currency=pos.contract.currency,
                    exchange=pos.contract.exchange,
                    is_active=True
                )
                db.add(db_position)
            
            synced_count += 1
        
        db.commit()
        return {"message": f"Synced {synced_count} positions from IBKR"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error syncing positions: {str(e)}")