using UnityEngine;
// Trigger behaviour for the sensors
public class SensorTrigger : MonoBehaviour
{
  public Agent parentAgent;
  public int sensorIndex;

  private void Start()
  {
    Debug.Log($"Sensor {sensorIndex} initialized. Layer: {LayerMask.LayerToName(gameObject.layer)}");
  }

  private void OnTriggerEnter(Collider other)
  {
    Debug.Log($"Sensor {sensorIndex} OnTriggerEnter. Other: {other.gameObject.name}, Layer: {LayerMask.LayerToName(other.gameObject.layer)}");
    int value = DetermineColliderType(other.gameObject.layer);
    parentAgent.UpdateSensorValue(sensorIndex, value);
  }

  private void OnTriggerExit(Collider other)
  {
    Debug.Log($"Sensor {sensorIndex} OnTriggerExit. Other: {other.gameObject.name}, Layer: {LayerMask.LayerToName(other.gameObject.layer)}");
    parentAgent.UpdateSensorValue(sensorIndex, 0);
  }
  private int DetermineColliderType(int layer)
  {
    if (layer == LayerMask.NameToLayer("Objects"))
      return 1; // Objects
    else if (layer == LayerMask.NameToLayer("Obstacles"))
      return 2; // Obstacles
    else if (layer == LayerMask.NameToLayer("Stacks"))
      return 3; // Stacks
    else
      return 0; // No collision or unknown layer
  }
}