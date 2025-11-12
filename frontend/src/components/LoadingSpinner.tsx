import '../styles/LoadingSpinner.css'

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner = ({ message = 'Carregando dados da F1...' }: LoadingSpinnerProps) => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  )
}

export default LoadingSpinner
