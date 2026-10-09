import Button from './Button'
import '../styles/ErrorMessage.css'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

const ErrorMessage = ({ message, onRetry }: ErrorMessageProps) => {
  return (
    <div className="error-container">
      <div className="error-icon">⚠️</div>
      <h3>Erro ao carregar dados</h3>
      <p>{message}</p>
      {onRetry && (
        <Button onClick={onRetry}>
          Tentar Novamente
        </Button>
      )}
    </div>
  )
}

export default ErrorMessage
