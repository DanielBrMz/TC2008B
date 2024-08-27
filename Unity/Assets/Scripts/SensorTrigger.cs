using UnityEngine;
// Trigger behaviour for the sensors
public class SensorTrigger : MonoBehaviour
{
  public Agent parentAgent;
  public char direction;

  private void OnTriggerEnter(Collider other)
  {
    int value = DetermineColliderType(other.gameObject.layer);

    if (parentAgent != null)
    {
      parentAgent.UpdateSensorValue(direction, value);
    } else 
    {
      Debug.LogError("The parent agent is not set correctly");
    }
  }

  private void OnTriggerExit(Collider other)
  {
    parentAgent.UpdateSensorValue(direction, 0);
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