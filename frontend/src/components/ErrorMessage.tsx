import Icon from './Icon'
import '../styles/ErrorMessage.css'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

const ErrorMessage = ({ message, onRetry }: ErrorMessageProps) => {
  return (
    <div className="error-container">
      <div className="error-icon"><Icon name="warning" size={48} /></div>
      <h3>Erro ao carregar dados</h3>
      <p>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="retry-button">
          <Icon name="refresh" size={16} />
          Tentar Novamente
        </button>
      )}
    </div>
  )
}

export default ErrorMessage
