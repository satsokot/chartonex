from datetime import datetime
from database import db


class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        row = Settings.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = Settings.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
            row.updated_at = datetime.utcnow()
        else:
            row = Settings(key=key, value=str(value))
            db.session.add(row)
        db.session.commit()


class PriceLog(db.Model):
    __tablename__ = 'price_logs'
    id = db.Column(db.Integer, primary_key=True)
    source_buy = db.Column(db.Float, nullable=True)
    source_sell = db.Column(db.Float, nullable=True)
    source_avg = db.Column(db.Float, nullable=True)
    dest_price = db.Column(db.Float, nullable=True)
    difference = db.Column(db.Float, nullable=True)
    sent_price = db.Column(db.Float, nullable=True)
    action_taken = db.Column(db.String(50), default='no_action')
    message_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'source_buy': self.source_buy,
            'source_sell': self.source_sell,
            'source_avg': self.source_avg,
            'dest_price': self.dest_price,
            'difference': self.difference,
            'sent_price': self.sent_price,
            'action_taken': self.action_taken,
            'message_id': self.message_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
